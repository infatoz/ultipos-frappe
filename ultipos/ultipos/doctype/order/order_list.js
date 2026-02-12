frappe.listview_settings["Order"] = {

    refresh(listview) {

        listview.page.add_inner_button("Auto Accept ON/OFF", () => {
            frappe.msgprint("Toggle from settings");
        });
    },

    formatters: {
        order_status(value, df, doc) {

            if (value === "New") {

                return `
                    <button class="btn btn-xs btn-success accept-btn"
                        data-name="${doc.name}">
                        Accept
                    </button>
                    <button class="btn btn-xs btn-danger deny-btn"
                        data-name="${doc.name}">
                        Deny
                    </button>
                `;
            }

            return value;
        }
    },

    onload(listview) {

        // Accept
        $(document).on("click", ".accept-btn", function () {

            const name = $(this).data("name");

            frappe.db.set_value("Order", name, {
                order_status: "Accepted"
            });
        });

        // Deny
        $(document).on("click", ".deny-btn", function () {

            const name = $(this).data("name");

            frappe.db.set_value("Order", name, {
                order_status: "Cancelled"
            });
        });
    }
};
