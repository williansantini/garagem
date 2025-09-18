# send_push.py
import sys
import json
from pywebpush import webpush, WebPushException

if __name__ == "__main__":
    try:
        subscription_json = sys.argv[1]
        payload_json = sys.argv[2]
        vapid_private_key = sys.argv[3]
        vapid_claims_email = sys.argv[4]

        subscription_data = json.loads(subscription_json)
        payload_data = json.loads(payload_json)

        webpush(
            subscription_info=subscription_data,
            data=json.dumps(payload_data),
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": f"mailto:{vapid_claims_email}"}
        )
    except WebPushException as ex:
        if ex.response and ex.response.status_code in [404, 410]:
            sys.exit(10) 
        sys.exit(1)
    except Exception:
        sys.exit(1)