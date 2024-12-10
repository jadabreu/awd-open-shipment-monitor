import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def format_week_label(date):
    """Convert date to format like 'OCT W40'"""
    month = date.strftime('%b').upper()
    week = date.strftime('%V')
    return f"{month} W{week}"

def get_week_dates(df):
    """Add formatted week labels and dates for analysis"""
    df['Week_Start'] = pd.to_datetime(df['Week'].apply(lambda x: f"{x}-1"), format='%G-W%V-%w')
    df['Week_Label'] = df['Week_Start'].apply(format_week_label)
    return df

def calculate_reception_metrics(df, start_date, end_date):
    """Calculate reception metrics for the given period"""
    mask = (df['Created  date'] >= start_date) & (df['Created  date'] < end_date)
    period_df = df[mask].copy()
    unique_shipments_df = period_df.drop_duplicates(subset=['Shipment ID'])
    unclosed_df = unique_shipments_df[~unique_shipments_df['Status'].isin(['Closed', 'Canceled'])]
    total_shipments = len(unclosed_df)
    total_shipped = period_df[~period_df['Status'].isin(['Closed', 'Canceled'])]['Shipped quantity '].sum()
    total_received = period_df[~period_df['Status'].isin(['Closed', 'Canceled'])]['Received quantity '].sum()
    unreceived_units = total_shipped - total_received
    reception_percentage = round((total_received / total_shipped * 100), 1) if total_shipped > 0 else 0
    return total_shipments, total_shipped, total_received, unreceived_units, reception_percentage

def analyze_shipment_status_distribution(df, start_date, end_date):
    """Analyze shipment status distribution for the given period"""
    # Filter data for the period
    mask = (df['Created  date'] >= start_date) & (df['Created  date'] < end_date)
    period_df = df[mask].copy()
    
    # Get unique shipments
    unique_shipments_df = period_df.drop_duplicates(subset=['Shipment ID'])
    active_shipments_df = unique_shipments_df[~unique_shipments_df['Status'].isin(['Closed', 'Canceled'])]
    
    # Calculate total shipments
    total_shipments = len(active_shipments_df)
    
    # Calculate shipments by status
    in_transit_shipments = len(active_shipments_df[active_shipments_df['Status'].isin(['In transit'])])
    partial_shipments = len(active_shipments_df[active_shipments_df['Status'].isin(['Checked in', 'Receiving'])])
    received_shipments = len(active_shipments_df[active_shipments_df['Received quantity '] >= active_shipments_df['Shipped quantity ']])
    
    # Calculate percentages
    in_transit_pct = round((in_transit_shipments / total_shipments * 100), 1) if total_shipments > 0 else 0
    partial_pct = round((partial_shipments / total_shipments * 100), 1) if total_shipments > 0 else 0
    received_pct = round((received_shipments / total_shipments * 100), 1) if total_shipments > 0 else 0
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=['In Transit', 'Partially Received', 'Fully Received'],
        y=[in_transit_pct, partial_pct, received_pct],
        text=[
            f'{in_transit_pct}%<br>({in_transit_shipments} shipments)', 
            f'{partial_pct}%<br>({partial_shipments} shipments)', 
            f'{received_pct}%<br>({received_shipments} shipments)'
        ],
        textposition='auto',
        marker_color=['#ff9900', '#d62728', '#2ca02c']  # Orange, Red, Green
    ))
    
    fig.update_layout(
        title=f'Shipment Status Distribution (Total: {total_shipments} Active Shipments)',
        yaxis_title='Percentage of Shipments',
        showlegend=False,
        height=400,
        yaxis=dict(range=[0, 100])  # Set y-axis range from 0 to 100%
    )
    
    return fig

def create_monthly_reception_progress(df, two_months_ago_start, two_months_ago_end, last_month_start, last_month_end, current_month_start, current_month_end):
    """Create a single figure with three gauge charts showing monthly reception progress"""
    # Create figure with subplots
    fig = make_subplots(
        rows=3, cols=1,
        specs=[[{'type': 'indicator'}], [{'type': 'indicator'}], [{'type': 'indicator'}]],
        vertical_spacing=0.2  # Increased spacing
    )
    
    # Add gauge for two months ago
    month_name = two_months_ago_start.strftime('%B')
    metrics = calculate_reception_metrics(df, two_months_ago_start, two_months_ago_end)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=metrics[4],  # reception_percentage
            number={'suffix': "%"},
            title={
                'text': f"{month_name} Inventory Reception Progress<br>({metrics[0]} Pending Shipments)<br><span style='font-size:0.8em'>Received Units: {int(metrics[2]):,} / Unreceived Units: {int(metrics[3]):,}</span>",
                'font': {'size': 14}
            },
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2ca02c"},
                'bgcolor': "#d62728",
                'borderwidth': 2,
                'steps': [{'range': [0, 100], 'color': "#d62728"}]
            }
        ),
        row=1, col=1
    )
    
    # Add gauge for last month
    month_name = last_month_start.strftime('%B')
    metrics = calculate_reception_metrics(df, last_month_start, last_month_end)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=metrics[4],  # reception_percentage
            number={'suffix': "%"},
            title={
                'text': f"{month_name} Inventory Reception Progress<br>({metrics[0]} Pending Shipments)<br><span style='font-size:0.8em'>Received Units: {int(metrics[2]):,} / Unreceived Units: {int(metrics[3]):,}</span>",
                'font': {'size': 14}
            },
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2ca02c"},
                'bgcolor': "#d62728",
                'borderwidth': 2,
                'steps': [{'range': [0, 100], 'color': "#d62728"}]
            }
        ),
        row=2, col=1
    )
    
    # Add gauge for current month
    month_name = current_month_start.strftime('%B')
    metrics = calculate_reception_metrics(df, current_month_start, current_month_end)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=metrics[4],  # reception_percentage
            number={'suffix': "%"},
            title={
                'text': f"{month_name} Inventory Reception Progress<br>({metrics[0]} Pending Shipments)<br><span style='font-size:0.8em'>Received Units: {int(metrics[2]):,} / Unreceived Units: {int(metrics[3]):,}</span>",
                'font': {'size': 14}
            },
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#2ca02c"},
                'bgcolor': "#d62728",
                'borderwidth': 2,
                'steps': [{'range': [0, 100], 'color': "#d62728"}]
            }
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=900,  # Increased height for vertical layout
        margin=dict(t=100, l=40, r=40, b=20)  # Increased top margin
    )
    
    return fig

def main():
    st.title("AWD to FBA Shipment Analysis")
    
    # Add report download instructions
    st.markdown("""
    ### To make the shipment analysis you need to download the AWD to FBA report. Here is how to get the Report:
    1. Go to [Amazon Seller Central Inventory](https://sellercentral.amazon.com/fba-inventory/gim/inventory-list)
    2. Click on the arrow next to "AWD Report"
    3. Select "Download Shipment Details"
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your Amazon shipments report (CSV/Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        # Read file based on extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
        
        # Convert date column to datetime
        df['Created  date'] = pd.to_datetime(df['Created  date'])
        
        # Extract ISO week number and ISO year
        df['Week'] = df['Created  date'].dt.strftime('%G-W%V')
        
        # Calculate date ranges
        today = datetime.now()
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        two_months_ago_start = (last_month_start - timedelta(days=1)).replace(day=1)
        
        # Calculate the first day of the next month for each period
        if two_months_ago_start.month == 12:
            two_months_ago_end = datetime(two_months_ago_start.year + 1, 1, 1)
        else:
            two_months_ago_end = datetime(two_months_ago_start.year, two_months_ago_start.month + 1, 1)
            
        if last_month_start.month == 12:
            last_month_end = datetime(last_month_start.year + 1, 1, 1)
        else:
            last_month_end = datetime(last_month_start.year, last_month_start.month + 1, 1)
            
        if current_month_start.month == 12:
            current_month_end = datetime(current_month_start.year + 1, 1, 1)
        else:
            current_month_end = datetime(current_month_start.year, current_month_start.month + 1, 1)
        
        # Monthly Reception Progress section
        st.header("Monthly Reception Progress")
        
        # Create and display combined gauge charts
        progress_fig = create_monthly_reception_progress(
            df,
            two_months_ago_start, two_months_ago_end,
            last_month_start, last_month_end,
            current_month_start, current_month_end
        )
        st.plotly_chart(progress_fig, use_container_width=True)
        
        # AWD Performance section
        st.header(f"AWD Detailed Performance {last_month_start.strftime('%B')}")
        st.markdown("#### *Note: Amazon only provide closed shipments info for the past month*")
        
        # Get performance metrics for last month
        status_fig = analyze_shipment_status_distribution(df, last_month_start, last_month_end)
        
        # Display metrics
        st.plotly_chart(status_fig, use_container_width=True)

if __name__ == "__main__":
    main()
