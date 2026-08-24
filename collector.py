import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = "https://www.sofascore.com/api/v1"
OUT = Path("data")
OUT.mkdir(exist_ok=True)


def get_json(page, url):
    print(f"Consultando: {url}")

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    page.wait_for_timeout(2000)

    body = page.locator("body").inner_text()

    if '"code":403' in body or '"reason":"challenge"' in body:
        raise RuntimeError(
            f"SofaScore retornou bloqueio 403 challenge: {url}"
        )

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Resposta não é JSON.\nPrimeiros caracteres:\n{body[:500]}"
        )


def collect(event_id):
    snapshot = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id,
    }

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        # Primeiro abrimos o site principal.
        # Isso permite que o navegador inicialize normalmente.
        print("Abrindo SofaScore...")

        page.goto(
            "https://www.sofascore.com/",
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.wait_for_timeout(5000)

        # Dados principais do evento
        snapshot["event"] = get_json(
            page,
            f"{BASE}/event/{event_id}"
        )

        # Estatísticas
        snapshot["statistics"] = get_json(
            page,
            f"{BASE}/event/{event_id}/statistics"
        )

        # Incidentes
        snapshot["incidents"] = get_json(
            page,
            f"{BASE}/event/{event_id}/incidents"
        )

        # Gráfico de pressão/momentum
        snapshot["graph"] = get_json(
            page,
            f"{BASE}/event/{event_id}/graph"
        )

        browser.close()

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    path = OUT / f"{event_id}_{timestamp}.json"

    path.write_text(
        json.dumps(
            snapshot,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(f"Snapshot salvo em: {path}")
    print("Coleta concluída com sucesso!")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Uso: python collector.py EVENT_ID")
        sys.exit(1)

    collect(sys.argv[1])
