function updateTime() {
    let now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes().toString().padStart(2, '0');
    let seconds = now.getSeconds().toString().padStart(2, '0'); // Get seconds and format with leading zero
    let period = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    document.getElementById('clockDisplay').textContent = `${hours}:${minutes}:${seconds} ${period}`;
}

setInterval(updateTime, 1000);

document.addEventListener('DOMContentLoaded', function() {
    function fetchWeatherData() {
        fetch('/weather')
            .then(response => response.json())
            .then(data => {
                let weatherForecastContainer = document.getElementById('weatherForecast');
                weatherForecastContainer.innerHTML = '';
                data.forEach(item => {
                    let forecastItem = document.createElement('div');
                    forecastItem.classList.add('weather-forecast-item');
                    let iconUrl = `http://openweathermap.org/img/wn/${item.icon_code}.png`;
                    let iconImg = document.createElement('img');
                    iconImg.src = iconUrl;
                    iconImg.alt = item.description;
                    let forecastContent = `
                        <b>${item.date}</b><br>
                        ${item.description}<br>
                        ${iconImg.outerHTML}
                        <br>
                        <b>Low:</b> ${item.low_temp}<br>
                        <b>High:</b> ${item.high_temp}
                    `;
                    forecastItem.innerHTML = forecastContent;
                    weatherForecastContainer.appendChild(forecastItem);
                });
            })
            .catch(error => console.error('Error fetching weather data:', error));
    }

    function fetchComparisonData() {
        fetch('/comparison')
            .then(response => response.json())
            .then(data => {
                let comparisonGrid = document.querySelector('.comparison-grid');
                comparisonGrid.innerHTML = '';
                data.forEach(person => {
                    let comparisonItem = document.createElement('div');
                    comparisonItem.classList.add('comparison-item');
                    let nameElement = document.createElement('h3');
                    nameElement.textContent = person.name;
                    comparisonItem.appendChild(nameElement);
                    let recoveryImg = document.createElement('img');
                    recoveryImg.src = person.recoveryImage;
                    recoveryImg.alt = `Recovery - ${person.name}`;
                    comparisonItem.appendChild(recoveryImg);
                    let sleepImg = document.createElement('img');
                    sleepImg.src = person.sleepImage;
                    sleepImg.alt = `Sleep - ${person.name}`;
                    comparisonItem.appendChild(sleepImg);
                    comparisonGrid.appendChild(comparisonItem);
                });
            })
            .catch(error => console.error('Error fetching comparison data:', error));
    }

    function fetchTaskData() {
        fetch('/tasks')
            .then(response => response.json())
            .then(data => {
                let tasksContainer = document.querySelector('.task-grid');
                tasksContainer.innerHTML = ''; // Clear existing content
    
                // Create an ordered list (ol) to hold the tasks
                let taskList = document.createElement('ol');
                taskList.classList.add('task-list');
    
                data.forEach((task, index) => {
                    // Create a list item (li) for each task
                    let taskItem = document.createElement('li');
                    taskItem.classList.add('task-item');
    
                    // Title (assuming task.id is the number)
                    let titleElement = document.createElement('h3');
                    titleElement.textContent = `${task.date}`;
    
                    // Description
                    let descriptionElement = document.createElement('p');
                    descriptionElement.textContent = task.task;
    
                    // Append title and description to the list item
                    taskItem.appendChild(titleElement);
                    taskItem.appendChild(descriptionElement);
    
                    // Append list item to the task list
                    taskList.appendChild(taskItem);
                });
    
                // Append the entire task list to the tasksContainer
                tasksContainer.appendChild(taskList);
            })
            .catch(error => console.error('Error fetching tasks:', error));
    }
    fetchWeatherData();
    fetchComparisonData();
    fetchTaskData();
});