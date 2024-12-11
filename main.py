import streamlit as st
import pandas as pd
from datetime import datetime
import io

def calculate_metrics(df, start_date, end_date):
    """Calculate metrics for a given date range"""
    # Filter data for the period
    mask = (df['Created  date'] >= start_date) & (df['Created  date'] < end_date)
    period_df = df[mask].copy()
    
    # Skip if no data for this period
    if len(period_df) == 0:
        return {
            'total_units_sent': 0,
            'total_units_received': 0,
            'open_shipments': 0,
            'total_units_in_os': 0,
            'units_received_os': 0,
            'units_not_received_os': 0
        }
    
    # Aggregate by shipment
    shipment_totals = period_df.groupby('Shipment ID').agg({
        'Shipped quantity ': 'sum',
        'Received quantity ': 'sum',
        'Status': lambda x: set(x)
    }).reset_index()
    
    # Calculate metrics
    total_units_sent = int(shipment_totals['Shipped quantity '].sum())
    total_units_received = int(shipment_totals['Received quantity '].sum())
    
    # Calculate open shipments metrics
    open_shipments = shipment_totals[shipment_totals['Received quantity '] < shipment_totals['Shipped quantity ']]
    total_units_in_os = int(open_shipments['Shipped quantity '].sum())
    units_received_os = int(open_shipments['Received quantity '].sum())
    units_not_received_os = total_units_in_os - units_received_os
    
    return {
        'total_units_sent': total_units_sent,
        'total_units_received': total_units_received,
        'open_shipments': len(open_shipments),
        'total_units_in_os': total_units_in_os,
        'units_received_os': units_received_os,
        'units_not_received_os': units_not_received_os
    }

def format_percentage(value, total, force_hundred=False):
    """Format percentage value"""
    if value == '':
        return ''
    if force_hundred and isinstance(value, (int, float)) and value > 0:
        return '100.0%'
    if isinstance(value, (int, float)) and total > 0:
        percentage = (value / total * 100)
        return f"{percentage:.1f}%"
    return ''

def format_number(value):
    """Format number with thousands separator"""
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return value

def main():
    st.title("AWD to FBA Shipment Stats")
    
    # Add report download instructions
    st.markdown("""
    ### To make the shipment analysis you need to download the AWD to FBA report. Here is how to get the Report:
    1. Go to [Amazon Seller Central Inventory](https://sellercentral.amazon.com/fba-inventory/gim/inventory-list)
    2. Click on the arrow next to "AWD Report"
    3. Select "Download Shipment Details"
    """)
    
    # File uploader
    uploaded_file = st.file_uploader("Upload your Amazon shipments report (Excel File) here:", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        # Read file based on extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=1)
        else:
            df = pd.read_excel(uploaded_file, skiprows=1)
        
        # Convert date column to datetime
        df['Created  date'] = pd.to_datetime(df['Created  date'])
        
        # Calculate date ranges
        today = datetime.now()
        current_month = today.replace(day=1)
        last_month = (current_month.replace(day=1) - pd.DateOffset(days=1)).replace(day=1)
        two_months_ago = (last_month.replace(day=1) - pd.DateOffset(days=1)).replace(day=1)
        
        # Calculate next month starts for ranges
        current_month_end = (current_month + pd.DateOffset(months=1))
        last_month_end = current_month
        two_months_ago_end = last_month
        
        # Calculate metrics for each period
        metrics_two_months_ago = calculate_metrics(df, two_months_ago, two_months_ago_end)
        metrics_last_month = calculate_metrics(df, last_month, last_month_end)
        metrics_current_month = calculate_metrics(df, current_month, current_month_end)
        
        # Calculate total non-received units for subtitle
        total_not_received = (metrics_two_months_ago['units_not_received_os'] + 
                            metrics_last_month['units_not_received_os'])
        total_units_in_os = (metrics_two_months_ago['total_units_in_os'] + 
                           metrics_last_month['total_units_in_os'])
        percentage_not_received = (total_not_received / total_units_in_os * 100) if total_units_in_os > 0 else 0
        
        # Display table title
        st.markdown("### AWD to FBA Shipment Stats")
        
        # Create display table data (formatted for Streamlit display)
        display_data = {
            'Metric': [
                'Total Units Sent',
                'Total Units Received',
                'Open Shipments (OS)',
                'Total Units in OS',
                'Units Received from OS',
                'Units Not Received from OS'
            ],
            f"{two_months_ago.strftime('%B')}": [
                '',  # Total Units Sent (only for last month)
                '',  # Total Units Received (only for last month)
                str(metrics_two_months_ago['open_shipments']),
                format_number(metrics_two_months_ago['total_units_in_os']),
                format_number(metrics_two_months_ago['units_received_os']),
                format_number(metrics_two_months_ago['units_not_received_os'])
            ],
            '%': [
                '',  # No data for this month
                '',  # No data for this month
                '',  # No percentage for open shipments count
                format_percentage(metrics_two_months_ago['total_units_in_os'], 1, True),
                format_percentage(metrics_two_months_ago['units_received_os'], metrics_two_months_ago['total_units_in_os']),
                format_percentage(metrics_two_months_ago['units_not_received_os'], metrics_two_months_ago['total_units_in_os'])
            ],
            f"{last_month.strftime('%B')}": [
                format_number(metrics_last_month['total_units_sent']),
                format_number(metrics_last_month['total_units_received']),
                str(metrics_last_month['open_shipments']),
                format_number(metrics_last_month['total_units_in_os']),
                format_number(metrics_last_month['units_received_os']),
                format_number(metrics_last_month['units_not_received_os'])
            ],
            '% ': [  # Note the space to make the column name unique
                '100.0%',  # Always 100% when data exists
                format_percentage(metrics_last_month['total_units_received'], metrics_last_month['total_units_sent']),
                '',  # No percentage for open shipments count
                format_percentage(metrics_last_month['total_units_in_os'], 1, True),
                format_percentage(metrics_last_month['units_received_os'], metrics_last_month['total_units_in_os']),
                format_percentage(metrics_last_month['units_not_received_os'], metrics_last_month['total_units_in_os'])
            ],
            f"{current_month.strftime('%B')}": [
                '',  # Total Units Sent (only for last month)
                '',  # Total Units Received (only for last month)
                str(metrics_current_month['open_shipments']),
                format_number(metrics_current_month['total_units_in_os']),
                format_number(metrics_current_month['units_received_os']),
                format_number(metrics_current_month['units_not_received_os'])
            ],
            '%  ': [  # Note the two spaces to make the column name unique
                '',  # No data for this month
                '',  # No data for this month
                '',  # No percentage for open shipments count
                format_percentage(metrics_current_month['total_units_in_os'], 1, True),
                format_percentage(metrics_current_month['units_received_os'], metrics_current_month['total_units_in_os']),
                format_percentage(metrics_current_month['units_not_received_os'], metrics_current_month['total_units_in_os'])
            ]
        }
        
        # Create export table data (raw numbers for Excel)
        export_data = {
            'Metric': display_data['Metric'],
            f"{two_months_ago.strftime('%B')}": [
                '',  # Total Units Sent (only for last month)
                '',  # Total Units Received (only for last month)
                metrics_two_months_ago['open_shipments'],
                metrics_two_months_ago['total_units_in_os'],
                metrics_two_months_ago['units_received_os'],
                metrics_two_months_ago['units_not_received_os']
            ],
            '%': [
                '',
                '',
                '',
                1 if metrics_two_months_ago['total_units_in_os'] > 0 else '',  # 100% as decimal
                (metrics_two_months_ago['units_received_os'] / metrics_two_months_ago['total_units_in_os']) if metrics_two_months_ago['total_units_in_os'] > 0 else '',
                (metrics_two_months_ago['units_not_received_os'] / metrics_two_months_ago['total_units_in_os']) if metrics_two_months_ago['total_units_in_os'] > 0 else ''
            ],
            f"{last_month.strftime('%B')}": [
                metrics_last_month['total_units_sent'],
                metrics_last_month['total_units_received'],
                metrics_last_month['open_shipments'],
                metrics_last_month['total_units_in_os'],
                metrics_last_month['units_received_os'],
                metrics_last_month['units_not_received_os']
            ],
            '% ': [
                1,  # 100% as decimal
                (metrics_last_month['total_units_received'] / metrics_last_month['total_units_sent']) if metrics_last_month['total_units_sent'] > 0 else '',
                '',
                1 if metrics_last_month['total_units_in_os'] > 0 else '',  # 100% as decimal
                (metrics_last_month['units_received_os'] / metrics_last_month['total_units_in_os']) if metrics_last_month['total_units_in_os'] > 0 else '',
                (metrics_last_month['units_not_received_os'] / metrics_last_month['total_units_in_os']) if metrics_last_month['total_units_in_os'] > 0 else ''
            ],
            f"{current_month.strftime('%B')}": [
                '',  # Total Units Sent (only for last month)
                '',  # Total Units Received (only for last month)
                metrics_current_month['open_shipments'],
                metrics_current_month['total_units_in_os'],
                metrics_current_month['units_received_os'],
                metrics_current_month['units_not_received_os']
            ],
            '%  ': [
                '',
                '',
                '',
                1 if metrics_current_month['total_units_in_os'] > 0 else '',  # 100% as decimal
                (metrics_current_month['units_received_os'] / metrics_current_month['total_units_in_os']) if metrics_current_month['total_units_in_os'] > 0 else '',
                (metrics_current_month['units_not_received_os'] / metrics_current_month['total_units_in_os']) if metrics_current_month['total_units_in_os'] > 0 else ''
            ]
        }
        
        # Create DataFrames
        display_df = pd.DataFrame(display_data)
        export_df = pd.DataFrame(export_data)
        
        # Display formatted table
        st.dataframe(display_df, use_container_width=True)
        
        # Display subtitle with totals
        st.markdown(f"Total non-received units from open shipments in {two_months_ago.strftime('%B')} and {last_month.strftime('%B')}: **{format_number(total_not_received)} units ({percentage_not_received:.1f}%)**")
        
        # Create Excel file
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Write original data to first sheet
            df.to_excel(writer, sheet_name='Raw Data', index=False)
            
            # Write summary to second sheet
            export_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Get workbook and formats
            workbook = writer.book
            
            # Format Raw Data sheet
            raw_worksheet = writer.sheets['Raw Data']
            raw_header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#f0f2f6',
                'border': 1
            })
            
            # Apply header format to Raw Data sheet
            for col_num, value in enumerate(df.columns.values):
                raw_worksheet.write(0, col_num, value, raw_header_format)
                raw_worksheet.set_column(col_num, col_num, 15)  # Set default width
            
            # Format Summary sheet
            summary_worksheet = writer.sheets['Summary']
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#f0f2f6',
                'border': 1
            })
            number_format = workbook.add_format({'num_format': '#,##0'})
            percentage_format = workbook.add_format({'num_format': '0.0%'})
            
            # Apply formats to Summary sheet
            for col_num, value in enumerate(export_df.columns.values):
                summary_worksheet.write(0, col_num, value, header_format)
            
            # Apply number formatting to data columns
            for col_num in [1, 3, 5]:  # Month columns
                summary_worksheet.set_column(col_num, col_num, 24, number_format)
            
            # Apply percentage formatting to percentage columns
            for col_num in [2, 4, 6]:  # Percentage columns
                summary_worksheet.set_column(col_num, col_num, 8, percentage_format)
            
            # Set metric column width in Summary sheet
            summary_worksheet.set_column(0, 0, 30)
            
            # Freeze panes on both sheets
            raw_worksheet.freeze_panes(1, 0)
            summary_worksheet.freeze_panes(1, 0)
        
        # Download button for Excel file
        st.download_button(
            label="📥 Download Complete Report (Excel)",
            data=buffer.getvalue(),
            file_name=f"AWD_FBA_Shipment_Stats_{today.strftime('%Y_%m_%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )

if __name__ == "__main__":
    main()
