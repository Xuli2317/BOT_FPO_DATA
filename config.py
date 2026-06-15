import os
ROOT_DIR = "SENTIMENT_INDEX"

BOT_DIR = os.path.join(ROOT_DIR, "BOT")
BOT_CODE_DIR = os.path.join(BOT_DIR, "CODE")

FPO_DIR = os.path.join(ROOT_DIR, "FPO")
FPO_CODE_DIR = os.path.join(FPO_DIR, "CODE")

CHECKPOINT_DIR = os.path.join(BOT_CODE_DIR, "checkpoint")
CAT_DIR = os.path.join(BOT_CODE_DIR, "category")
SE_DIR = os.path.join(BOT_CODE_DIR, "series")
OB_DIR = os.path.join(BOT_CODE_DIR, "observations")

CODE_DIR = os.path.join(ROOT_DIR, "CODE")
UPLOAD_CHECKPOINT_DIR = os.path.join(CODE_DIR, "checkpoint")

for d in [
    ROOT_DIR,
    BOT_DIR,
    BOT_CODE_DIR,
    FPO_DIR,
    FPO_CODE_DIR,
    CHECKPOINT_DIR,
    CAT_DIR,
    SE_DIR,
    OB_DIR,
    CODE_DIR,
    UPLOAD_CHECKPOINT_DIR
]:
    os.makedirs(d, exist_ok=True)
