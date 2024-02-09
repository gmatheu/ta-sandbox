import streamlit as st
from datetime import timedelta
from typing import Dict, Tuple

import streamlit as st
st.set_page_config(
    page_title="TA Sandbox",
    page_icon=":dollar:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def intro():
    import streamlit as st

    st.write("# Welcome to Streamlit! 👋")
    st.sidebar.success("Select a demo above.")

    st.markdown(
        """
        Streamlit is an open-source app framework built specifically for
        Machine Learning and Data Science projects.

        **👈 Select a demo from the dropdown on the left** to see some examples
        of what Streamlit can do!

        ### Want to learn more?

        - Check out [streamlit.io](https://streamlit.io)
        - Jump into our [documentation](https://docs.streamlit.io)
        - Ask a question in our [community
          forums](https://discuss.streamlit.io)

        ### See more complex demos

        - Use a neural net to [analyze the Udacity Self-driving Car Image
          Dataset](https://github.com/streamlit/demo-self-driving)
        - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
    """
    )


def plotting_demo():
    import streamlit as st
    import time
    import numpy as np

    st.markdown(f'# {list(page_names_to_funcs.keys())[1]}')
    st.write(
        """
        This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!
"""
    )

    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    last_rows = np.random.randn(1, 1)
    chart = st.line_chart(last_rows)

    for i in range(1, 101):
        new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
        status_text.text("%i%% Complete" % i)
        chart.add_rows(new_rows)
        progress_bar.progress(i)
        last_rows = new_rows
        time.sleep(0.05)

    progress_bar.empty()

    # Streamlit widgets automatically run the script from top to bottom. Since
    # this button is not connected to any other logic, it just causes a plain
    # rerun.
    st.button("Re-run")


def summary():
    from notebooks.alerts import all_trades, TradeSet
    import streamlit as st
    import pandas as pd
    import altair as alt

    from urllib.error import URLError

    st.markdown(f"# {list(page_names_to_funcs.keys())[0]}")
    st.write(""" """)

    tickers_sets = {
        'global': [
            'GOOG',
            "NVDA",
            "SATL",
            "TSLA",
            "GOLD",
            "NFLX",
            "FCX",
            "BABA",
            "META",
            "MELI",
            "INTC",
            "AMD",
            "NKE",
            "AMZN",
            "MSFT",
            "PBR",
            "MARA",
            "SPCE",
            "FSLR",
            "PLUG",
            "PHUN",
            "RUN",
            "SCATC.OL",
            "CHPT",
            "SEDG",
            "MDB",
            "HAL"
        ],
        'cedears': [
            "NVDAD.BA",
            "SATLD.BA",
            "TSLAD.BA",
            "GOLDD.BA",
            "GOGLD.BA",
            "NFLXD.BA",
            # "FCXD.BA",
            "BABAD.BA",
            "METAD.BA",
            "MELID.BA",
            "INTCD.BA",
            "AMDD.BA",
            "TSLAD.BA",
            "NKED.BA",
            "AMZND.BA",
            "MSFTD.BA",
            "PBRD.BA",
        ],
        'etf': [
            'GBS.L',
            'PHSP.L',
            'AIVL',
            'AIEQ',
            'GLD',
            'IAU',
            'ROBO',
            'BOTZ',
            'SOXX',
            'LIT',
            'EMQQ',
            'GBTC'
        ]
    }
    ticker_set = st.sidebar.selectbox("Ticker set", tickers_sets.keys())
    timeframe = "D"
    tickers = tickers_sets.get(ticker_set, tickers_sets['global'])

    @st.cache_data(ttl=timedelta(hours=24))
    def get_all_trades(tickers) -> Dict[str, TradeSet]:
        return all_trades(tickers, timeframe, cache=False)

    try:
        for group_tickers in tickers_sets.values():
            get_all_trades(group_tickers)

        selected_trades = get_all_trades(tickers)
        selected_tickers = st.multiselect(
            "Choose tickers", tickers, tickers
        )
        if not selected_tickers:
            st.error("Please select at least one ticker.")
        else:
            st.write("#### Signals")

            with st.expander("Signals", expanded=True):
                with st.container():
                    col1, col2 = st.columns(2)
                    col1.markdown("### Long and Short Trends")
                    col1.markdown(
                        "**Trends** are either a _Trend_ (```1```) or _No Trend_ (```0```) depending on the **Trend** passed into ***Trend Signals**")
                    col1.markdown("The **Trades** are either _Enter_ (```1```) or _Exit_ (```-1```) or _No Position/Action_ (```0```). These are based on the **Trend** passed into **Trend Signals** whether they are _Long_ or _Short_ Trends.")

                    col2.markdown(
                        "### Buy and Hold Returns (*PCTRET_1*) vs. Cum. Active Returns (*ACTRET_1*)")
                st.markdown("### Entries Last Week")
                for ticker in selected_tickers:
                    (trades, _, _, _) = selected_trades[ticker]
                    trades = trades.reset_index()
                    last_week = pd.to_datetime('today') - pd.Timedelta(weeks=1)
                    last_entry = trades[trades['Signal'] == 1].tail(1)['Date']
                    if last_entry.values[0] > last_week:
                        st.markdown(
                            f"Symbol: *{ticker}* [Yahoo!](https://finance.yahoo.com/quote/{ticker}/chart?p={ticker})"
                        )
                        st.write(trades[trades['Signal'] == 1].tail(1))

                st.markdown("### Signals")
                for ticker in selected_tickers:
                    (trades, trendy, asset, long) = selected_trades[ticker]

                    def create_signals_chart():
                        trades = trendy.TS_Trades.tail(30)

                        source = trades.rename(
                            'signal').to_frame().reset_index()
                        source['symbol'] = ticker

                        chart = alt.Chart(source).mark_area(opacity=0.5).encode(
                            x=alt.X("Date:T").timeUnit(
                                "yearmonthdate").title("date"),
                            y="signal",
                            color=alt.Color("symbol")
                        ).properties(
                            height=150,
                        )
                        return chart
                    signals_chart = create_signals_chart()

                    def create_trend_chart():
                        long_trend = trendy.TS_Trends.tail(30)

                        source = long_trend.rename(
                            'signal').to_frame().reset_index()
                        source['symbol'] = ticker

                        chart = alt.Chart(source).mark_line(point=True).encode(
                            x=alt.X("Date:T").timeUnit(
                                "yearmonthdate").title("date"),
                            y="signal",
                            color=alt.Color("symbol:N")
                        ).properties(
                            height=150,
                        )
                        return chart
                    trend_chart = create_trend_chart()

                    returns = (
                        (asset.tail(30)[["PCTRET_1", "ACTRET_1"]] + 1).cumprod() - 1).reset_index()

                    def create_actret_chart():
                        source = returns

                        chart = alt.Chart(source).mark_area(opacity=0.7).encode(
                            x=alt.X("Date:T").timeUnit(
                                "yearmonthdate").title("date"),
                            y="ACTRET_1"
                        )
                        pctret_chart = alt.Chart(source).mark_line(point=True).encode(
                            x=alt.X("Date:T").timeUnit(
                                "yearmonthdate").title("date"),
                            y="PCTRET_1"
                        )
                        return chart + pctret_chart
                    actret_chart = create_actret_chart()

                    tradingv_view_symbol = ticker
                    st.markdown(
                        f"Symbol: *{ticker}* [TradingView](https://www.tradingview.com/chart/KRY341eq/?symbol={tradingv_view_symbol}) / [Yahoo!](https://finance.yahoo.com/quote/{ticker}/chart?p={ticker})"
                    )
                    with st.container():
                        col1, col2 = st.columns(2)
                        col1.altair_chart(
                            trend_chart + signals_chart, use_container_width=True)
                        col2.altair_chart(
                            actret_chart, use_container_width=True)

            st.write("#### Tickers")
            with st.expander("Tickers", expanded=False):
                for ticker in selected_tickers:
                    (trades, trendy, asset, long) = selected_trades[ticker]

                    # chart = asset[["close", "EMA_10", "EMA_20", "EMA_50"]]
                    # chart.plot(subplots=False, figsize=(16, 10), color=colors("BkGrOrRd"), title=ptitle, grid=True)

                    source = asset.tail(180).reset_index()
                    close_chart = (
                        alt.Chart(source)
                        .mark_line()
                        .encode(
                            x="Date:T",
                            y=alt.Y("close:N")
                        )
                    )
                    ema10_chart = (
                        alt.Chart(source)
                        .mark_line()
                        .encode(
                            x="Date:T",
                            y=alt.Y("EMA_10:N")
                        )
                    )
                    st.markdown(f"#### Ticker: {ticker}")
                    with st.container():
                        col1, col2 = st.columns(2)
                        col1.write(asset)
                        col2.altair_chart(
                            close_chart + ema10_chart, use_container_width=True)
    except URLError as e:
        st.error(
            """
            **This demo requires internet access.**

            Connection error: %s
        """
            % e.reason
        )


def data_frame_demo():
    import streamlit as st
    import pandas as pd
    import altair as alt

    from urllib.error import URLError

    st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")
    st.write(
        """
        This demo shows how to use `st.write` to visualize Pandas DataFrames.

(Data courtesy of the [UN Data Explorer](http://data.un.org/Explorer.aspx).)
"""
    )

    @st.cache_data
    def get_UN_data():
        AWS_BUCKET_URL = "http://streamlit-demo-data.s3-us-west-2.amazonaws.com"
        df = pd.read_csv(AWS_BUCKET_URL + "/agri.csv.gz")
        return df.set_index("Region")

    try:
        df = get_UN_data()
        countries = st.multiselect(
            "Choose countries", list(df.index), [
                "China", "United States of America"]
        )
        if not countries:
            st.error("Please select at least one country.")
        else:
            data = df.loc[countries]
            data /= 1000000.0
            st.write("### Gross Agricultural Production ($B)",
                     data.sort_index())

            data = data.T.reset_index()
            data = pd.melt(data, id_vars=["index"]).rename(
                columns={"index": "year",
                         "value": "Gross Agricultural Product ($B)"}
            )
            chart = (
                alt.Chart(data)
                .mark_area(opacity=0.3)
                .encode(
                    x="year:T",
                    y=alt.Y("Gross Agricultural Product ($B):Q", stack=None),
                    color="Region:N",
                )
            )
            st.altair_chart(chart, use_container_width=True)
    except URLError as e:
        st.error(
            """
            **This demo requires internet access.**

            Connection error: %s
        """
            % e.reason
        )


page_names_to_funcs = {
    "Summary": summary,
    "Dataframe demo": data_frame_demo,
    "—": intro,
    "Plotting Demo": plotting_demo
}

demo_name = st.sidebar.selectbox("Choose a demo", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()
