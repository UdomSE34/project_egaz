import os

media_dirs = [
    "media/payment_slips",
    "media/payment_receipts",
    "media/monthly_reports/payment",
    "media/monthly_reports/waste",
]

for d in media_dirs:
    os.makedirs(d, exist_ok=True)

print("All MEDIA folders ensured.")
