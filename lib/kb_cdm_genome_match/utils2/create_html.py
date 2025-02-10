import pandas as pd
import logging
logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)

def create_datatable_html(csv_filepath, output_filepath="datatable.html", rows_per_page=10):
    """
    Reads a CSV file, generates an HTML page with an interactive DataTable using DataTables.js,
    and saves it to the specified output file.

    Args:
        csv_filepath (str): Path to the input CSV file.
        output_filepath (str): Path to save the generated HTML file (default: "datatable.html").
        rows_per_page (int): Number of rows to display per page in the DataTable (default: 10).
    """

    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
        return
    except pd.errors.ParserError as e:
        print(f"Error: Could not parse CSV file at {csv_filepath}: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    # HTML template with placeholders for the table data
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive DataTable</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.dataTables.min.css">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/select/1.7.0/css/select.dataTables.min.css">
        <style>
            /* Optional: Basic styling for better readability */
            body {{
                font-family: sans-serif;
            }}
            #datatable-container {{
                width: 95%; /* Adjust as needed */
                margin: 20px auto;
            }}
        </style>
    </head>
    <body>
        <div id="datatable-container">
            <table id="datatable" class="display compact" style="width:100%">
                <thead>
                    <tr>
                        {''.join(f'<th>{col}</th>' for col in df.columns)}
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'<tr>{"".join(f"<td>{row[col]}</td>" for col in df.columns)}</tr>' for _, row in df.iterrows())}
                </tbody>
                <tfoot>
                    <tr>
                        {''.join(f'<th>{col}</th>' for col in df.columns)}
                    </tr>
                </tfoot>
            </table>
        </div>

        <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
        <script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/select/1.7.0/js/dataTables.select.min.js"></script>
        <script>
            $(document).ready(function() {{
                $('#datatable').DataTable( {{
                    dom: 'Bfrtip', // Defines the order of table controls
                    buttons: [
                        'colvis', // Column visibility
                        'copy', // Copy to clipboard
                        'excel', // Export to Excel
                        'csv',   // Export to CSV
                        'pdf',   // Export to PDF
                        'print'  // Print
                    ],
                    select: true, // Enable row selection
                    pageLength: {rows_per_page}, // Initial page length
                    lengthMenu: [ 10, 25, 50, 100 ], // Page length options
                    scrollX: true,
                     //Column definitions to enable search in footer
                    initComplete: function () {{
                        this.api()
                            .columns()
                            .every(function () {{
                                let column = this;
                                let title = column.header().textContent;

                                // Create input element
                                let input = document.createElement('input');
                                input.placeholder = title;
                                column.footer().replaceChildren(input);

                                // Event listener for user input
                                input.addEventListener('keyup', () => {{
                                    if (column.search() !== this.value) {{
                                        column
                                            .search(input.value)
                                            .draw();
                                    }}
                                }});
                            }});
                    }},
                }} );
            }} );
        </script>
    </body>
    </html>
    """

    # Write the HTML to the output file
    try:
        with open(output_filepath, "w") as f:
            f.write(html)
        print(f"DataTable HTML saved to {output_filepath}")
    except Exception as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    # Replace 'merged.csv' with the actual path to your CSV file
    csv_filepath = "merged.csv"  # Use the local file
    html_file_path = "datatable.html"
    create_datatable_html(csv_filepath, html_file_path, rows_per_page=50)  # Generate with 50 rows per page

