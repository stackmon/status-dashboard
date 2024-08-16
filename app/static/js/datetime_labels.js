const formatDateTimeWithTimeZone = (date) => {
  if (isNaN(date.getTime())) return 'Invalid Date';

  const options = {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
    hour12: false,
  };

  const localDateTime = new Intl.DateTimeFormat('en-GB', options).format(date);
  return localDateTime.replace(/(\d{2})\/(\d{2})\/(\d{4}), (\d{2}:\d{2}) (.+)/, '$3-$2-$1 $4 $5');
};

const updateDateLabels = () => {
  document.querySelectorAll('.datetime').forEach((element) => {
    const dateTimeStr = element.textContent;
    const dateTimeUTC = new Date(dateTimeStr);
    element.textContent = formatDateTimeWithTimeZone(dateTimeUTC);
  });
};

updateDateLabels();
