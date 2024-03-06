document.addEventListener('DOMContentLoaded', function() {
    setInterval(sendFormData, 50000);
});
function sendFormData() {
    let form = document.getElementById('createForm');
    let formData = new FormData(form);
    const domEditableElement = document.querySelector('.ck-editor__editable');
    if (domEditableElement && domEditableElement.ckeditorInstance) {
        const editorInstance = domEditableElement.ckeditorInstance;
        let editorData = editorInstance.getData();
        formData.set('text', editorData);
    }
    fetch(autosaveUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => console.log('Data autosaved'))
    .catch(error => console.error('Error during autosave', error));
}