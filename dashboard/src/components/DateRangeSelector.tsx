import React, { useState, useEffect } from 'react';

interface DateRangeSelectorProps {
  onDatesChange: (startDate: string, endDate: string) => void;
  initialStartDate?: string;
  initialEndDate?: string;
}

const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  onDatesChange,
  initialStartDate = '',
  initialEndDate = ''
}) => {
  const [startDate, setStartDate] = useState<string>(initialStartDate);
  const [endDate, setEndDate] = useState<string>(initialEndDate);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (initialStartDate) setStartDate(initialStartDate);
    if (initialEndDate) setEndDate(initialEndDate);
  }, [initialStartDate, initialEndDate]);

  const handleApply = () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date cannot be after end date');
      return;
    }

    setError('');
    onDatesChange(startDate, endDate);
  };

  return (
    <div className="date-range-selector">
      <h3>Select Date Range</h3>
      <div className="date-inputs">
        <div>
          <label htmlFor="startDate">Start Date:</label>
          <input
            type="date"
            id="startDate"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="endDate">End Date:</label>
          <input
            type="date"
            id="endDate"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <button onClick={handleApply}>Apply Dates</button>
    </div>
  );
};

export default DateRangeSelector;