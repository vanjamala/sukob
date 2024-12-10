from fastagency import FastAgency
from fastagency.ui.mesop import MesopUI

from ..workflow import wf

app = FastAgency(
    provider=wf,
    ui=MesopUI(),
    title="sukob",
)

# start the fastagency app with the following command
# gunicorn sukob.local.main_mesop:app
