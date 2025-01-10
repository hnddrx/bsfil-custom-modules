const { Component, whenReady, xml, mount, onMounted } = owl;

class PrintComponent extends Component {
  // Class property to store fetched employee data
  employeeData = [];
  docName = '';

  setup() {
    // Fetch employee data when the component is mounted
    onMounted(() => {
      this.fetchEmployeeData();
    });
  }

  async fetchEmployee201(data){
    /* let extractedData = employeeData.employee[1]
    console.log('Extracted Data', extractedData) */
    try {
        const employeeData =  this.employeeData
        console.log('Employee Data',  employeeData)
        const url = '/web/dataset/call_kw'; // Odoo's JSON-RPC endpoint

        const requestPayload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "hr.employee",
                "method": "search_read",
                "args": [], // args can be left empty since domain is provided in kwargs
                "kwargs": {
                    
                   
                }
            }
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestPayload),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            console.error('Error in Odoo response:', data.error);
            return;
        }

        this.employeeData = data.result || []; // Store fetched data in component state, or empty array if null
        console.log('Fetched employee data:', this.employeeData);

    } catch (error) {
        console.error("Error fetching employee data:", error);
    }
  }

  async fetchEmployeeData() {
    try {
        // Retrieve text using XPath
        const textNode = document.evaluate(
            '/html/body/div[1]/div/div/div[1]/div/div[1]/div[2]/div/div[1]/span',
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;

        const text = textNode ? textNode.textContent.trim() : '';
        if (!text) {
            console.warn('Text content is empty or could not be retrieved.');
            return; // Exit if `text` is empty or undefined
        }

        console.log('Document name to search:', text);

        const url = '/web/dataset/call_kw'; // Odoo's JSON-RPC endpoint

        const requestPayload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "certificate.of.employment",
                "method": "search_read",
                "args": [], // args can be left empty since domain is provided in kwargs
                "kwargs": {
                    "fields": ["id", "doc_name", "company_id", "employee" ,"department", "first_name", "last_name", "type", "purpose"],
                    "domain": [["doc_name", "=", text]]
                }
            }
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestPayload),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) {
            console.error('Error in Odoo response:', data.error);
            return;
        }

        this.employeeData = data.result || []; // Store fetched data in component state, or empty array if null
        console.log('Fetched employee data:', this.employeeData);

    } catch (error) {
        console.error("Error fetching employee data:", error);
    }
}

  async onPrint() {

    if (!this.employeeData || this.employeeData.length === 0) {
      console.error("No employee data available to print.");
      alert("Employee data is not available to print."); // Show an alert to the user
      return; // Exit the function if no data
    }
  
    const printWindow = window.open('', '', 'width=800,height=600'); // Open a new window
  
    // Write the content to the new window, including employee data
    const employee = this.employeeData[0];
    console.log('Employee Data on Print',this.employeeData[0])

    printWindow.document.write(`
     <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate of Employment</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #000;
        }
        .container {
            padding: 20px;
            width: 700px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
        }
        .header img {
            width: 200px;
            margin-bottom: 10px;
        }
        .header p {
            margin: 5px;
            font-size: 12px;
        }
        .title {
            text-align: center;
            font-weight: bold;
            background-color: #F5A14E;
            padding: 10px;
            margin-top: 20px;
            font-size: 16px;
        }
        .content {
            margin-top: 20px;
            line-height: 1.6;
        }
        .content p {
            margin: 5px 0;
        }
        .label {
            font-weight: bold;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
        }
        .footer .date,
        .footer .manager-info {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://via.placeholder.com/200x50?text=LOGO" alt="Company Logo">
            <p>135 Sgt Rivera Cor Banawe Sts Brgy Manresa Quezon City</p>
            <p>Tel: 8362-2080  Fax: 8362-2083</p>
        </div>

        <div class="title">
            CERTIFICATE OF EMPLOYMENT
        </div>

        <div class="content">
            <p>This is to certify that.</p>
            <p><span class="label">Name:</span> ${employee.first_name} ${employee.last_name}</p>
            <p><span class="label">Designation:</span> MARKETING STAFF</p>
            <p><span class="label">Department:</span> ${employee.department}</p>
            <p><span class="label">Remarks:</span> ${employee.type}</p>
            <p><span class="label">Employment Period:</span> From <strong>SEPTEMBER 11, 2023</strong> TO <strong>MARCH 23, 2024</strong> only</p>

            <p>This certification is being issued upon the request of Mr./Ms. ${employee.last_name} for ${ employee.purpose === 'Travel Abroad' ? 'travel abroad purpose only.' : 'whatever legal purpose it may serve.'}</p>

            <p style="text-align: center; margin-top: 20px;">
                -----------------------------------NOTHING FOLLOWS-----------------------------------
            </p>

            <div class="footer">
                <div class="date">Quezon City, April 05, 2024.</div>

                <div class="manager-info">
                    Ma.Fe M. Galicia<br>
                    Human Resources & Admin Manager
                </div>

                <p>This certificate is not valid if data has been changed or tampered.</p>
            </div>
        </div>
    </div>
</body>
</html>

    `);
  
    printWindow.document.close(); // Close the document writing
    printWindow.focus(); // Focus the new window
    printWindow.print(); // Trigger the print dialog
    printWindow.close(); // Close the print window after printing
  }
  
}

// Define the template for the PrintComponent
PrintComponent.template = xml`
  <button t-on-click="onPrint" class="btn btn-success">
    Print
  </button>
`;

// Function to mount the component or observe the DOM
function mountComponent() {
  const jsElement = document.querySelector('.js_template_using_owl');

  if (jsElement instanceof HTMLElement) {
    // Ensure jsElement is a valid DOM element before attempting to mount the component
    mount(PrintComponent, {
      target: jsElement
    });
  } else {
    // Create a MutationObserver to wait for the element to appear
    const observer = new MutationObserver(() => {
      const foundElement = document.querySelector('.js_template_using_owl');

      if (foundElement instanceof HTMLElement) {
        console.log('Found Element', foundElement)
        // Ensure foundElement is a valid DOM element before attempting to mount the component
        mount(PrintComponent, foundElement);
        observer.disconnect(); // Stop observing once the element is found and component is mounted
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }
}

// Wait until the DOM is fully loaded
window.onload = () => whenReady(mountComponent);
