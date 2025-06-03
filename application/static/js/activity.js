document.addEventListener('DOMContentLoaded', function() {
            const userSelect = document.getElementById('userSelect');
            const showChartBtn = document.getElementById('showChartBtn');
            const chartImage = document.getElementById('chartImage');
            const loadingIndicator = document.getElementById('loadingIndicator');
            const currentYearSpan = document.getElementById('currentYear');
            
            // Устанавливаем текущий год
            currentYearSpan.textContent = new Date().getFullYear();
            
            // Функция обновления графика
            async function updateChart() {
                const username = userSelect.value;
                
                // Показываем индикатор загрузки
                showChartBtn.disabled = true;
                loadingIndicator.style.display = 'block';
                chartImage.style.display = 'none';
                
                try {
                    // Отправляем запрос на сервер
                    const formData = new FormData();
                    formData.append('username', username);
                    
                    const response = await fetch('/todo/plot.png', {
                        method: 'POST',
                        body: new URLSearchParams(`username=${username}`),
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }
                    });
                    
                    if (!response.ok) {
                        throw new Error('Ошибка загрузки графика');
                    }
                    
                    // Получаем изображение
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    
                    // Обновляем изображение на странице
                    chartImage.src = imageUrl;
                    chartImage.alt = `Активность пользователя ${username}`;
                    chartImage.style.display = 'block';
                    
                } catch (error) {
                    console.error('Ошибка:', error);
                    chartImage.alt = 'Ошибка при загрузке графика';
                    chartImage.style.display = 'block';
                } finally {
                    // Скрываем индикатор загрузки
                    showChartBtn.disabled = false;
                    loadingIndicator.style.display = 'none';
                }
            }
            
            // Обработчики событий
            showChartBtn.addEventListener('click', updateChart);
            userSelect.addEventListener('change', updateChart);
            
            // Автоматически загружаем график для первого пользователя
            if (userSelect.options.length > 0) {
                updateChart();
            }
        });
