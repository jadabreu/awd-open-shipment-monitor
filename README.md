# AWD to FC Analysis

A Streamlit application for analyzing Amazon AWD (Amazon Warehouse Deals) shipments to FC (Fulfillment Centers). This tool provides insights into shipment reception progress and status distribution.

## Features

- Monthly reception progress tracking with gauge charts
- Shipment status distribution analysis
- Support for CSV and Excel report formats
- Interactive visualizations

## Setup

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/awd-open-shipment-monitor.git
cd awd-open-shipment-monitor
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run main.py
```

## How to Get the AWD Report

1. Go to [Amazon Seller Central Inventory](https://sellercentral.amazon.com/fba-inventory/gim/inventory-list)
2. Click on the arrow next to "AWD Report"
3. Select "Download Shipment Details"
4. Upload the downloaded report to the application

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- Plotly
