{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyPo316vZYCqTSQDbZxYxCce",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Xuli2317/BOT_FPO_DATA/blob/main/config.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "import os\n",
        "ROOT_DIR = \"SENTIMENT_INDEX\"\n",
        "\n",
        "BOT_DIR = os.path.join(ROOT_DIR, \"BOT\")\n",
        "BOT_CODE_DIR = os.path.join(BOT_DIR, \"CODE\")\n",
        "\n",
        "FPO_DIR = os.path.join(ROOT_DIR, \"FPO\")\n",
        "FPO_CODE_DIR = os.path.join(FPO_DIR, \"CODE\")\n",
        "\n",
        "CHECKPOINT_DIR = os.path.join(BOT_CODE_DIR, \"checkpoint\")\n",
        "CAT_DIR = os.path.join(BOT_CODE_DIR, \"category\")\n",
        "SE_DIR = os.path.join(BOT_CODE_DIR, \"series\")\n",
        "OB_DIR = os.path.join(BOT_CODE_DIR, \"observations\")\n",
        "\n",
        "CODE_DIR = os.path.join(ROOT_DIR, \"CODE\")\n",
        "UPLOAD_CHECKPOINT_DIR = os.path.join(CODE_DIR, \"checkpoint\")\n",
        "\n",
        "for d in [\n",
        "    ROOT_DIR,\n",
        "    BOT_DIR,\n",
        "    BOT_CODE_DIR,\n",
        "    FPO_DIR,\n",
        "    FPO_CODE_DIR,\n",
        "    CHECKPOINT_DIR,\n",
        "    CAT_DIR,\n",
        "    SE_DIR,\n",
        "    OB_DIR,\n",
        "    CODE_DIR,\n",
        "    UPLOAD_CHECKPOINT_DIR\n",
        "]:\n",
        "    os.makedirs(d, exist_ok=True)"
      ],
      "metadata": {
        "id": "HkqHM82FC4gT"
      },
      "execution_count": null,
      "outputs": []
    }
  ]
}