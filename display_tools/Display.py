"""Display of the result of the model """

import plotly.graph_objects as go
from datetime import datetime, timedelta

def create_agenda_plot(start_date, end_date):
    fig = go.Figure()

    current_date = start_date

    while current_date <= end_date:
        time_slot_start = datetime(current_date.year, current_date.month, current_date.day, 8, 0)  # Start at 8:00 AM
        time_slot_end = datetime(current_date.year, current_date.month, current_date.day, 23, 45)  # End at 11:45 PM

        while time_slot_start < time_slot_end:
            fig.add_trace(go.Scatter(x=[time_slot_start, time_slot_start + timedelta(minutes=15)],
                                     y=[current_date.strftime('%Y-%m-%d %H:%M:%S')] * 2,
                                     line=dict(color='blue', width=6)))
            time_slot_start += timedelta(minutes=15)

        current_date += timedelta(days=1)

    fig.update_layout(title_text='Agenda',
                      xaxis=dict(title='Time'),
                      yaxis=dict(title='Date'),
                      showlegend=False)

    fig.show()

# Example usage
start_date = datetime(2024, 3, 8)  # Replace with your desired start date
end_date = datetime(2024, 3, 10)   # Replace with your desired end date
print('ok')
create_agenda_plot(start_date, end_date)
