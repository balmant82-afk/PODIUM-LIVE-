import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


OUT = Path("data")
OUT.mkdir(exist_ok=True)


def collect(event_id):

    snapshot = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "event_id": event_id,
        "responses": []
    }

    with sync_playwright() as p:

        print("Abrindo navegador...")

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="pt-BR"
        )

        page = context.new_page()

        def capture_response(response):

            url = response.url

            if "/api/" not in url:
                return

            print(f"API encontrada: {url}")

            try:

                if response.status == 200:

                    data = response.json()

                    snapshot["responses"].append({
                        "url": url,
                        "status": response.status,
                        "data": data
                    })

                    print(
                        f"OK: {url}"
                    )

                else:

                    print(
                        f"API retornou {response.status}: {url}"
                    )

            except Exception as e:

                print(
                    f"Não foi possível ler resposta: {e}"
                )

        page.on(
    "request",
    lambda request: print(f"REQUEST: {request.url}")
)

        match_url = (
            f"https://www.sofascore.com/"
            f"hellas-verona-u20-cesena-u20/"
            f"bLFgsgLFg#id:{event_id}"
        )

        print("Abrindo página do jogo...")

        page.goto(
            match_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Página do jogo aberta.")

        print(f"Título: {page.title()}")
        print(f"Conteúdo da página: {page.locator('body').inner_text()[:1000]}")

        print("Aguardando carregamento dos dados...")

        page.wait_for_timeout(15000)

        print(
            f"Total de respostas API capturadas: "
            f"{len(snapshot['responses'])}"
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

    print("")
    print("==============================")
    print("COLETA CONCLUÍDA")
    print(f"Arquivo: {path}")
    print("==============================")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Uso: python collector.py EVENT_ID"
        )

        sys.exit(1)

    collect(sys.argv[1])
