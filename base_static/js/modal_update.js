document.addEventListener('DOMContentLoaded', () => {
    let form_confirm = document.querySelector('#form_confirm_update_modal')
    let buttons = document.querySelectorAll("[data-target='#itemUpdateModal']");
    const fieldMap = {
        first_name: 'firstName',
        last_name: 'lastName',
        email: 'email',
        age: 'age',
        status: 'status',
        revenue: 'revenue',
        category: 'category',
        agent: 'agent',
    };

    const setFieldValue = (name, value) => {
        const field = form_confirm.querySelector(`[name="${name}"]`);

        if (field) {
            field.value = value || '';
        }
    };

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            if (button.dataset.url) {
                form_confirm.action = button.dataset.url;
            }

            Object.entries(fieldMap).forEach(([fieldName, datasetName]) => {
                setFieldValue(fieldName, button.dataset[datasetName]);
            });
        })
    });
    let confirmModal = document.getElementById("confirmUpdateButtonModal")
    confirmModal.addEventListener('click', () => {
        form_confirm.submit();
    });
});
