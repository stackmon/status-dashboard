document.addEventListener('DOMContentLoaded', () => {
  const incidentImpact = document.getElementById('incidentImpact').value;

  if (incidentImpact == 0) {
    updateMaintenanceFields();
  } else {
    updateDateLabel();
  }

  const selectElement = document.querySelector('select');
  if (selectElement) {
    selectElement.addEventListener('change', (event) => {
      const selectedValue = event.target.value;

      if (incidentImpact == 0) {
        updateMaintenanceFields(event.target);
      } else {
        updateDateLabel(event.target);
      }
    });
  }
});

const updateDateLabel = (selectElement) => {
  const selectedValue = selectElement ? selectElement.value : '';
  const updateDateLabel = document.getElementById('updateDateLabel');
  const updateDateDiv = document.getElementById('updateDateDiv');

  if (updateDateLabel && updateDateDiv) {
    switch (selectedValue) {
      case 'resolved':
      case 'completed':
      case 'changed':
        updateDateLabel.innerText = 'End Date:';
        updateDateDiv.style.display = 'block';
        break;
      case 'reopened':
      case 'modified':
        updateDateDiv.style.display = 'none';
        if (selectedValue === 'changed') {
          updateDateLabel.innerText = 'End Date:';
        }
        break;
      default:
        updateDateLabel.innerText = 'Next Update by:';
        updateDateDiv.style.display = 'block';
        break;
    }
  }
};

const updateMaintenanceFields = (selectElement) => {
  const selectedValue = selectElement ? selectElement.value : '';
  const maintenanceStartDiv = document.getElementById('maintenanceStartDiv');
  const maintenanceEndDiv = document.getElementById('maintenanceEndDiv');
  console.log(incidentImpact)

  if (maintenanceStartDiv && maintenanceEndDiv) {
    if (selectedValue === 'modified' && incidentImpact == 0) {
      maintenanceStartDiv.style.display = 'block';
      maintenanceEndDiv.style.display = 'block';
    } else {
      maintenanceStartDiv.style.display = 'none';
      maintenanceEndDiv.style.display = 'none';
    }
  }
};
