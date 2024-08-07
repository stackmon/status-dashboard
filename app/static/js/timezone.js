document.addEventListener('DOMContentLoaded', () => {
  const timezoneField = document.getElementById('timezone');
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  if (timezoneField) {
    timezoneField.value = timezone;
  }
});
