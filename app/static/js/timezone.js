document.addEventListener('DOMContentLoaded', () => {
  const timezoneField = document.getElementById('timezone');
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  if (timezoneField) {
    timezoneField.value = timezone;

  }

  const date = new Date();
  const timezoneName = new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone,
      timeZoneName: 'short'
  }).formatToParts(date).find(part => part.type === 'timeZoneName').value;

  const timezoneInfoElements = document.querySelectorAll('.timezone-info');
  timezoneInfoElements.forEach(element => {
    element.textContent = `${timezoneName}`;
  });
});
