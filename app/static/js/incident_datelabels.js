const updateDateLabel = (selectElement) => {
  const selectedValue = selectElement ? selectElement.value : '';
  const updateDateLabelElement = document.getElementById('updateDateLabelElement');
  const updateDateDiv = document.getElementById('updateDateDiv');
  const updateMessageDiv = document.getElementById('updateMessageDiv');

  if (updateDateLabelElement && updateDateDiv && updateMessageDiv) {
    switch (selectedValue) {
      case 'reopened':
        updateMessageDiv.style.display = 'block';
        updateDateDiv.style.display = 'none';
        break;
      default:
        updateDateLabelElement.innerText = 'Update date:';
        updateDateDiv.style.display = 'block';
        updateMessageDiv.style.display = 'block';
        break;
      case 'Choose status..':
        updateDateLabelElement.innerText = 'Update date:';
        updateDateDiv.style.display = 'block';
        updateMessageDiv.style.display = 'block';
        break;
    }
  }
};

const updateMaintenanceFields = (selectElement) => {
  const selectedValue = selectElement ? selectElement.value : '';
  const updateDateLabelElement = document.getElementById('updateDateLabelElement');
  const updateDateDiv = document.getElementById('updateDateDiv');
  const maintenanceStartDiv = document.getElementById('maintenanceStartDiv');
  const maintenanceEndDiv = document.getElementById('maintenanceEndDiv');
  const updateMessageDiv = document.getElementById('updateMessageDiv');
  

  if (maintenanceStartDiv && maintenanceEndDiv && updateMessageDiv) {
    switch (selectedValue) {
      case 'modified':
        maintenanceStartDiv.style.display = 'block';
        maintenanceEndDiv.style.display = 'block';
        updateDateDiv.style.display = 'none';
        break;
      case 'completed':
        maintenanceEndDiv.style.display = 'none';
        maintenanceStartDiv.style.display = 'none';
        updateDateDiv.style.display = 'block';
        break;
      default:
        maintenanceStartDiv.style.display = 'none';
        maintenanceEndDiv.style.display = 'none';
        updateDateDiv.style.display = 'block';
        updateDateLabelElement.innerText = 'Update date:';
        break;
    }
  }
};
