"""
Portfolio dashboard for personal finances.
"""  # noqa: N999

from collections.abc import Callable
from logging import getLogger

import pytz
import streamlit as st
from streamlit.components.v1 import html

from finlit.data import Ledger
from finlit.data.datasets import NetworthHistoryDataset
from finlit.data.transformations.portfolio_assets import PorfolioAssets
from finlit.utils import create_parser, setup_logger, style_css
from finlit.viz.portfolio.holdings_piechart import holdings_chart
from finlit.viz.portfolio.networth_chart import networth_chart

tz = pytz.timezone("America/Argentina/Cordoba")

st.set_page_config(
    page_title="Personal Finances Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded",
)

parser = create_parser()
args = parser.parse_args()
setup_logger(verbose=args.verbose)
logger = getLogger()
ledger = Ledger(args.ledger)

#######################
# CSS styling

st.markdown(style_css, unsafe_allow_html=True)

# Center in div all objects with class stPlotlyChart
# and the parent div
st.markdown(
    """
  <style>
    .center-content {
      display: flex;
      justify-content: center;
      align-items: center;
    }

  </style>
    """,
    unsafe_allow_html=True,
)

#######################
# Sidebar

st.title("Portfolio")

#######################

# Dataframes

#######################

portfolio_assets = PorfolioAssets(ledger)
p_df = portfolio_assets.build()
p_df = p_df[p_df.asset_class != "currency"]
p_df["portfolio"] = p_df["portfolio"].apply(
    lambda x: "Sin portfolio" if not x or x == "" else x.capitalize()
)


def creater_filter_func(portfolio: str) -> Callable:
    """
    Create a filter function for the portfolio.
    """

    def filter_func(x) -> bool:  # noqa: ANN001
        prefix = f"Assets:Inversiones:{portfolio}"

        return x.account.lower()[: len(prefix)] == prefix.lower()

    return filter_func


# Filter by portfolio equal to global
global_porfolio = p_df.loc[p_df["portfolio"] == "Global"]
argy_porfolio = p_df.loc[p_df["portfolio"] == "Argentina"]

# Investment history
investment_history = NetworthHistoryDataset(ledger)

argy_func = creater_filter_func("ARG")
global_func = creater_filter_func("US")

# All investments
investment_history_df = investment_history.build(investments=True)
# Argentina investments
argy_investment_history_df = investment_history.build(
    investments=True, filter_func=argy_func
)
# Global investments
global_investment_history_df = investment_history.build(
    investments=True, filter_func=global_func
)

#######################

# Layout

#######################

cols = st.columns(spec=[3, 1])

with cols[0]:
    nw_chart = networth_chart(
        investment_history_df, global_investment_history_df, argy_investment_history_df
    )
    st.subheader("Invested assets")
    st.altair_chart(nw_chart, use_container_width=True, theme="streamlit")  # type: ignore[]

with cols[1]:
    p_piechart = holdings_chart(
        p_df, "Complete Portfolio", subportfolio=False, tags=True
    )
    st.altair_chart(p_piechart, use_container_width=True, theme="streamlit")  # type: ignore[]

    pg_piechart = holdings_chart(
        global_porfolio, "Global Portfolio", subportfolio=True, tags=True
    )
    st.altair_chart(pg_piechart, use_container_width=True, theme="streamlit")  # type: ignore[]

    pa_piechart = holdings_chart(
        argy_porfolio, "Argentina Portfolio", subportfolio=True, tags=True
    )
    st.altair_chart(pa_piechart, use_container_width=True, theme="streamlit")  # type: ignore[]


#######################

# Finish CSS

#######################

html(
    """
<script>
function centerPlotly() {
  // Element streamlit plotly
  element = parent.document.querySelector(".stPlotlyChart");

  if (element) {
    let parent = element.parentElement;
    while (parent) {
      // Find column parent
      if (parent.matches('div[data-testid="stVerticalBlock"]')) {
        // Finding all children that contain the plotly chart
        const children = parent.querySelectorAll(
          'div[data-testid="element-container"]',
        );

        // Centering all children
        children.forEach((child) => {
          child.classList.add("center-content");
        });
        break;
      }
      parent = parent.parentElement;
    }
  }
}

setInterval(centerPlotly, 1000);

</script>
""",
    height=0,
    width=0,
)

