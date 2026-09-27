"""Private dashboard API; bind to loopback behind the existing HTTPS proxy."""
from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
import threading
import time
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
import json
import secrets

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .dashboard_data import MAX_UPLOAD, read_report, reports_in
from src.arbitrage.engine import ArbitrageEngine
from src.arbitrage.exporter import export_arbitrage_excel
from src.finance.currency import get_usd_brl_rate
from src.config import load_config


def create_app(
    report_dir: str | None = None,
    access_key: str | None = None,
    secure: bool | None = None,
    auth_disabled: bool | None = None,
) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    directory = Path(report_dir or os.getenv('RADAR_REPORT_DIR', 'reports'))
    directory.mkdir(parents=True, exist_ok=True)
    
    if auth_disabled is None:
        env_auth_disabled = os.getenv('RADAR_AUTH_DISABLED', '').lower() in ('true', '1', 'yes')
        env_no_key = os.getenv('RADAR_DASHBOARD_KEY', '') in ('', 'none', 'disabled')
        auth_disabled = env_auth_disabled or (access_key is None and env_no_key)

    secret = access_key or os.getenv('RADAR_DASHBOARD_KEY', '')
    if not auth_disabled:
        if not secret:
            env = os.getenv('RADAR_ENV', 'development')
            if env == 'production':
                raise RuntimeError('RADAR_DASHBOARD_KEY deve conter pelo menos 24 caracteres em produção.')
            secret = 'radar-dev-access-key-minimum-24-chars'
        elif len(secret) < 24:
            raise RuntimeError('RADAR_DASHBOARD_KEY deve conter pelo menos 24 caracteres.')
    else:
        if not secret:
            secret = 'radar-public-access-no-auth-bypass-key'

    lock = threading.Lock()
    attempts: dict[str, list[float]] = {}
    cache: dict = {}

    @app.middleware('http')
    async def security(request: Request, call_next):
        if request.method == 'POST' and request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Origem não permitida.'}, status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    def check_cookie_valid(cookie: str) -> bool:
        if auth_disabled:
            return True
        if not cookie:
            return False
        try:
            expires, signature = cookie.split('.', 1)
            expected = hmac.new(secret.encode(), expires.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return False
            if int(expires) < time.time():
                return False
            return True
        except (ValueError, TypeError):
            return False

    def authorized(request: Request):
        if auth_disabled:
            return
        cookie = request.cookies.get('radar_session', '')
        if not check_cookie_valid(cookie):
            raise HTTPException(401, 'Entre com sua chave de acesso ao painel.')

    @app.get('/radar/api/session')
    def get_session(request: Request):
        if auth_disabled:
            return {'authenticated': True}
        cookie = request.cookies.get('radar_session', '')
        is_auth = check_cookie_valid(cookie)
        return {'authenticated': is_auth}

    @app.post('/radar/api/session')
    async def session(request: Request):
        if auth_disabled:
            return JSONResponse({'ok': True})
        if int(request.headers.get('content-length', 0)) > 2048:
            raise HTTPException(413, 'Requisição muito grande.')
        ip = request.client.host if request.client else 'unknown'
        now = time.time()
        attempts[ip] = [t for t in attempts.get(ip, []) if now - t < 60]
        if len(attempts[ip]) >= 10:
            raise HTTPException(429, 'Muitas tentativas. Aguarde um minuto.')
        attempts[ip].append(now)
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(400, 'Formato JSON inválido.')
        if not hmac.compare_digest(str(payload.get('key', '')), secret):
            raise HTTPException(401, 'Chave de acesso incorreta.')
        expiry = str(int(now + 30 * 86400))
        signature = hmac.new(secret.encode(), expiry.encode(), hashlib.sha256).hexdigest()
        response = JSONResponse({'ok': True})
        
        # Determine secure cookie flag
        if secure is not None:
            use_secure = secure
        else:
            is_https = (request.url.scheme == 'https') or (request.headers.get('x-forwarded-proto') == 'https')
            env_secure = os.getenv('RADAR_COOKIE_SECURE', '').lower()
            if env_secure in ('true', '1'):
                use_secure = True
            elif env_secure in ('false', '0'):
                use_secure = False
            else:
                use_secure = is_https

        response.set_cookie(
            'radar_session',
            expiry + '.' + signature,
            httponly=True,
            secure=use_secure,
            samesite='lax',
            path='/radar',
            max_age=30 * 86400
        )
        return response

    @app.post('/radar/api/logout')
    def logout():
        response = JSONResponse({'ok': True})
        response.delete_cookie('radar_session', path='/radar')
        return response

    @app.get('/radar/api/data', dependencies=[Depends(authorized)])
    def data():
        with lock:
            fingerprint = tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(directory.glob('*.xlsx')))
            if cache.get('fingerprint') != fingerprint:
                runs, skipped = reports_in(directory)
                cache.update(fingerprint=fingerprint, payload={'runs': runs, 'skipped': skipped})
            return cache['payload']

    @app.post('/radar/api/import', dependencies=[Depends(authorized)])
    async def upload(request: Request):
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > MAX_UPLOAD:
                raise HTTPException(413, 'O arquivo deve ter no máximo 10 MB.')
        fd, name = tempfile.mkstemp(suffix='.upload', dir=directory)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(content)
            temp = Path(name)
            xlsx = temp.with_suffix('.xlsx.pending')
            os.replace(temp, xlsx)
            report = read_report(xlsx)
            destination = directory / ('import_' + hashlib.sha256(report['id'].encode()).hexdigest()[:24] + '.xlsx')
            with lock:
                existing, _ = reports_in(directory)
                if any(r['id'] == report['id'] for r in existing):
                    return {'duplicate': True, 'id': report['id']}
                os.replace(xlsx, destination)
            return {'duplicate': False, 'id': report['id']}
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        except Exception as exc:
            raise HTTPException(422, 'Não foi possível ler o XLSX. Use um relatório válido do Radar.') from exc
        finally:
            Path(name).unlink(missing_ok=True)
            Path(name).with_suffix('.xlsx.pending').unlink(missing_ok=True)

    @app.get('/radar/api/reports/{run_id}', dependencies=[Depends(authorized)])
    def download(run_id: str):
        runs, _ = reports_in(directory)
        for run in runs:
            if run['id'] == run_id:
                return FileResponse(directory / run['filename'], filename=run['filename'])
        raise HTTPException(404, 'Relatório não encontrado.')

    @app.get('/radar/api/arbitrage', dependencies=[Depends(authorized)])
    def get_arbitrage_scans():
        scans = []
        for json_file in sorted(directory.glob('arbitrage_*.json'), reverse=True):
            try:
                data = json.loads(json_file.read_text(encoding='utf-8'))
                scans.append(data)
            except Exception:
                pass
        return {'scans': scans}

    @app.post('/radar/api/arbitrage/scan', dependencies=[Depends(authorized)])
    async def run_arbitrage_scan(request: Request):
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(400, 'Payload inválido.')

        query = str(payload.get('query', '')).strip()
        if not query:
            raise HTTPException(400, 'Informe um termo para escanear.')

        source = str(payload.get('source', 'alibaba'))
        limit = min(30, max(3, int(payload.get('limit', 15))))
        max_moq = int(payload.get('max_moq', 500))

        cfg = load_config()
        rate_info = get_usd_brl_rate(fallback_rate=cfg.DEFAULT_USD_BRL)
        engine = ArbitrageEngine(
            usd_rate=rate_info.rate,
            icms_rate=cfg.DEFAULT_ICMS_RATE,
            import_tax_rate=0.60,
            marketplace_fee_rate=cfg.DEFAULT_MARKETPLACE_FEE
        )

        try:
            report = engine.scan(query=query, source=source, max_items=limit, max_moq=max_moq)
        except Exception as e:
            raise HTTPException(500, f'Falha ao escanear: {str(e)}')

        scan_id = secrets.token_hex(8)
        report_data = asdict(report)
        report_data['id'] = scan_id
        report_data['date'] = datetime.now(timezone.utc).isoformat()
        report_data['filename'] = f'arbitrage_{scan_id}.xlsx'

        # Save excel
        excel_path = directory / report_data['filename']
        export_arbitrage_excel(report, output_path=excel_path)

        # Save json
        json_path = directory / f'arbitrage_{scan_id}.json'
        json_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')

        return report_data

    @app.get('/radar/api/arbitrage/download/{scan_id}', dependencies=[Depends(authorized)])
    def download_arbitrage(scan_id: str):
        target = directory / f'arbitrage_{scan_id}.xlsx'
        if target.exists():
            return FileResponse(target, filename=f'arbitragem_{scan_id}.xlsx')
        raise HTTPException(404, 'Relatório de arbitragem não encontrado.')

    # --- Trend Radar endpoints ---
    import os as _os
    from src.trends.repository import TrendRepository as _TrendRepo

    def _get_trend_repo():
        db_path = _os.getenv("MERCADO_LIVRE_DB_PATH", "data/mercado_livre_radar.db")
        repo = _TrendRepo(db_path)
        repo.initialize()
        return repo

    @app.get('/radar/api/trends', dependencies=[Depends(authorized)])
    def get_trends(strategy: str = "", category: str = "", limit: int = 100):
        repo = _get_trend_repo()
        items = repo.get_trending(
            strategy=strategy or None,
            category=category or None,
            limit=min(limit, 200),
        )
        # Enrich with sparkline
        for item in items:
            item["sparkline"] = repo.get_sparkline(
                item["product_id"], item["source"], points=30
            )
        return {"items": items}

    @app.get('/radar/api/trends/stats', dependencies=[Depends(authorized)])
    def get_trend_stats():
        repo = _get_trend_repo()
        return repo.get_stats()

    @app.get('/radar/api/trends/terms', dependencies=[Depends(authorized)])
    def get_trend_terms():
        repo = _get_trend_repo()
        terms = repo.get_active_terms()
        return {"terms": [{"id": t.id, "term": t.term, "category": t.category,
                           "source": t.source} for t in terms]}

    @app.get('/radar/api/trends/{product_id}/history', dependencies=[Depends(authorized)])
    def get_trend_history(product_id: str, source: str = "aliexpress"):
        repo = _get_trend_repo()
        history = repo.get_product_history(product_id, source)
        return {"history": history}

    dist = Path(os.getenv('RADAR_DIST_DIR', 'dashboard/dist'))
    if dist.exists():
        app.mount('/radar', StaticFiles(directory=dist, html=True), name='dashboard')
    return app
