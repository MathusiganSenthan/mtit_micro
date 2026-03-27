import json
import time

import httpx


def main() -> None:
    base = "http://localhost:8000"
    ts = int(time.time())
    email = f"user{ts}@example.com"

    with httpx.Client(timeout=20.0) as client:
        register = client.post(
            f"{base}/auth/register",
            json={"email": email, "password": "secret123"},
        )
        register.raise_for_status()
        access_token = register.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        product = client.post(
            f"{base}/products",
            headers=headers,
            json={
                "title": "MTIT Demo Book",
                "author": "Team 6",
                "isbn": f"9780132350{ts}",
                "price": 25.5,
                "stock": 10,
                "category": "technology",
            },
        )
        product.raise_for_status()
        product_id = product.json()["id"]

        order = client.post(
            f"{base}/orders",
            headers=headers,
            json={
                "items": [{"product_id": product_id, "quantity": 2}],
                "shipping_address": "Colombo",
                "notes": "assignment-demo",
            },
        )
        order.raise_for_status()

        print(
            json.dumps(
                {
                    "email": email,
                    "product_id": product_id,
                    "order_id": order.json()["id"],
                    "order_status": order.json()["status"],
                    "total": order.json()["total_amount"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
