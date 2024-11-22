from flask import Flask, request, render_template, send_file
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Performance Tracker</title>
        <!-- Bootstrap CSS -->
        <link
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css"
            rel="stylesheet"
            integrity="sha384-rbsA2VBKQvZrHRFe/0C4FzjUAN6mqeGkCV9sdTg5F5Wll4H/XVfKnEGLwlkWjJg"
            crossorigin="anonymous"
        >
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">Stock Tracker</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/">Home</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/download_excel">Download Excel</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/about">About</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        <div class="container text-center mt-5">
            <h1 class="mb-4">Stock Performance Tracker</h1>
            <form action="/stock" method="get" class="d-flex justify-content-center">
                <input type="text" id="ticker" name="ticker" class="form-control me-2" placeholder="Enter tickers (e.g., AAPL, MSFT)" required>
                <button type="submit" class="btn btn-primary">Get Data</button>
            </form>
        </div>
        <!-- Footer -->
        <footer class="bg-light text-center text-lg-start mt-5">
            <div class="container p-4">
                <p class="text-muted mb-0">© 2024 Stock Performance Tracker. All Rights Reserved.</p>
            </div>
        </footer>
        <!-- Bootstrap JS Bundle -->
        <script
            src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-ENjdO4Dr2bkBIFxQpeoYz1GaN6cVo8sG8rNoe/ljH/+BJwQx2ZWv7XfWo/nE6M4"
            crossorigin="anonymous"
        ></script>
    </body>
    </html>
    """

@app.route('/stock', methods=['GET'])
def stock():
    tickers = request.args.get('ticker')  # Get input tickers from the form
    print(f"Tickers received: {tickers}")  # Debugging: Log raw input tickers

    try:
        # Validate and clean ticker input
        ticker_list = [ticker.strip().upper() for ticker in tickers.split(',')]
        print(f"Ticker list: {ticker_list}")  # Debugging: Log cleaned ticker list

        # Handle empty or invalid input
        if not ticker_list or all(t == "" for t in ticker_list):
            return "Error: No valid tickers provided. <br> <a href='/'>Back to Home</a>"

        all_data = []  # Store data for each ticker
        all_graphs = []  # Store graphs for each ticker

        for ticker in ticker_list:
            if ticker:  # Ensure the ticker is not empty
                try:
                    stock_data = yf.Ticker(ticker)
                    info = stock_data.info

                    # Retry if data is empty
                    if not info or 'shortName' not in info:
                        print(f"Retrying ticker: {ticker}")
                        stock_data = yf.Ticker(ticker)
                        info = stock_data.info

                    if not info or 'shortName' not in info:
                        raise ValueError(f"No data found for ticker: {ticker}")

                    # Extract relevant info
                    data = {
                        "Ticker": ticker,
                        "Name": info.get("shortName", "N/A"),
                        "Current Price": info.get("currentPrice", "N/A"),
                        "Previous Close": info.get("regularMarketPreviousClose", "N/A"),
                        "Sector": info.get("sector", "N/A"),
                        "Industry": info.get("industry", "N/A"),
                        "Country": info.get("country", "N/A"),
                        "52-Week High": info.get("fiftyTwoWeekHigh", "N/A"),
                        "52-Week Low": info.get("fiftyTwoWeekLow", "N/A"),
                        "Dividend Rate": info.get("dividendRate", "N/A"),
                        "Earnings Date": info.get("earningsDate", "N/A"),
                        "Market Open": info.get("regularMarketOpen", "N/A"),
                    }
                    all_data.append(data)

                    # Fetch historical price data
                    hist_data = stock_data.history(period="1y")
                    hist_data.reset_index(inplace=True)

                    # Create a Plotly line chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist_data['Date'],
                        y=hist_data['Close'],
                        mode='lines',
                        name=f'{ticker} Close Price'
                    ))
                    fig.update_layout(
                        title=f"1-Year Historical Prices for {data['Name']} ({data['Ticker']})",
                        xaxis_title='Date',
                        yaxis_title='Price (USD)',
                        template='plotly_white'
                    )
                    all_graphs.append(fig.to_html(full_html=False))

                except Exception as e:
                    print(f"Error with ticker {ticker}: {e}")
                    return f"Error: Unable to fetch data for ticker {ticker}. <br> <a href='/'>Back to Home</a>"

        print(f"Data being passed to template: {all_data}")
        print(f"Graphs being passed to template: {len(all_graphs)} graphs generated.")

        # Save stock data globally for Excel export
        global stock_data_for_excel
        stock_data_for_excel = pd.DataFrame(all_data)  # Convert to a pandas DataFrame

        return render_template('stock.html', all_data=all_data, all_graphs=all_graphs, zip=zip)

    except Exception as e:
        print(f"General error: {e}")
        return f"Error: Unable to fetch data. Please check the tickers and try again. <br> <a href='/'>Back to Home</a>"

@app.route('/download_excel')
def download_excel():
    try:
        # Save DataFrame to a temporary Excel file
        excel_file = "stock_data.xlsx"
        stock_data_for_excel.to_excel(excel_file, index=False)
        return send_file(excel_file, as_attachment=True)
    except Exception as e:
        print(f"Error generating Excel file: {e}")
        return "Error: Unable to generate Excel file. Please try again later."

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
