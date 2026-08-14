import shutil

import pytest

from historical_campaign import HISTORICAL_CAMPAIGN_ROOT


@pytest.fixture
def historical_campaign_root(tmp_path):
    campaign_root = tmp_path / "historical_reference"
    shutil.copytree(HISTORICAL_CAMPAIGN_ROOT, campaign_root)
    return campaign_root
