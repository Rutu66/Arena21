

// index page


        let isSwiping = false;
        let startX;
        let currentX;
        const minSwipeDistance = 100;
        const swipeHandle = document.getElementById('swipeHandle');
        const swipeWrapper = document.getElementById('swipeWrapper');
        const swipeText = document.getElementById('swipeText');
    
        function startSwipe(event) {
            isSwiping = true;
            startX = event.clientX || event.touches[0].clientX; // Support for both mouse and touch
            swipeWrapper.classList.add('swiping');
            document.addEventListener('mousemove', swipeMove);
            document.addEventListener('mouseup', endSwipe);
            document.addEventListener('touchmove', swipeMove, { passive: false });  // Updated touch support
            document.addEventListener('touchend', endSwipe);    // Touch support
        }
    
        function swipeMove(event) {
            if (!isSwiping) return;
            currentX = event.clientX || event.touches[0].clientX; // Support for both mouse and touch
            let diffX = currentX - startX;
    
            if (diffX > 0 && diffX <= swipeWrapper.offsetWidth - swipeHandle.offsetWidth) {
                swipeHandle.style.left = `${diffX}px`;
                swipeText.style.opacity = 1 - (diffX / swipeWrapper.offsetWidth);
                event.preventDefault(); // Prevent default touch behavior like scrolling
            }
        }
    
        function endSwipe(event) {
            if (!isSwiping) return;
            isSwiping = false;
            let diffX = currentX - startX;
    
            if (diffX > swipeWrapper.offsetWidth / 2) {
                // Complete the swipe and submit the form
                swipeHandle.style.left = `${swipeWrapper.offsetWidth - swipeHandle.offsetWidth}px`;
                document.getElementById('orderForm').submit();
                setTimeout(resetSwipe, 1000); // Delay for reset after submission
            } else {
                // Revert the swipe
                resetSwipe();
            }
    
            swipeWrapper.classList.remove('swiping');
            document.removeEventListener('mousemove', swipeMove);
            document.removeEventListener('mouseup', endSwipe);
            document.removeEventListener('touchmove', swipeMove);  // Updated touch support
            document.removeEventListener('touchend', endSwipe);    // Touch support
        }
        
        
    
        function resetSwipe() {
            swipeHandle.style.left = '12px'; // Reset to initial position
            swipeText.style.opacity = 1;
        }
    
        // Attach event listeners
        swipeHandle.addEventListener('mousedown', startSwipe);
        swipeHandle.addEventListener('touchstart', startSwipe, { passive: true }); // Updated touch support
    
        function openForm(eventId, responseType, title) {
            currentEventId = eventId; // Store the event ID
            document.getElementById('betForm').style.display = 'block';
            document.getElementById('questionTitle').innerText = title; // Set the title
            document.getElementById('event_id').value = eventId;
            setResponse(responseType);
        }
        
    
        function closeForm() {
            document.getElementById('betForm').style.display = 'none';
        }
    
        function setResponse(responseType) {
            document.getElementById('response').value = responseType;
            if (responseType === 'yes') {
                document.getElementById('yesButton').classList.add('active');
                document.getElementById('noButton').classList.remove('active');
                swipeWrapper.classList.add('active');
                swipeWrapper.classList.remove('no-active');
            } else {
                document.getElementById('noButton').classList.add('active');
                document.getElementById('yesButton').classList.remove('active');
                swipeWrapper.classList.add('no-active');
                swipeWrapper.classList.remove('active');
            }
            calculateAmounts();
            fetchData(responseType);
        }
    
        function calculateAmounts() {
            var price = document.getElementById('price').value;
            var quantity = document.getElementById('quantity').value;
            document.getElementById('putAmount').innerText = (price * quantity).toFixed(2);
            document.getElementById('getAmount').innerText = (10 * quantity).toFixed(2);
        }
    
        document.getElementById('price').addEventListener('input', function() {
            document.getElementById('priceValue').value = this.value;
            calculateAmounts();
        });
    
        document.getElementById('quantity').addEventListener('input', function() {
            document.getElementById('quantityValue').value = this.value;
            calculateAmounts();
        });
    
        document.getElementById('priceValue').addEventListener('input', function() {
            document.getElementById('price').value = this.value;
            calculateAmounts();
        });
    
        document.getElementById('quantityValue').addEventListener('input', function() {
            document.getElementById('quantity').value = this.value;
            calculateAmounts();
        });
    
        function fetchData(responseType) {
            const orderTableBody = document.getElementById('orderTableBody');
            orderTableBody.innerHTML = ''; // Clear existing rows
        
            fetch(`/fetch-order-data/?response_type=${responseType}&event_id=${currentEventId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(order => {
                        let row = `<tr><td>${order.price_per_quantity}</td><td>${order.quantity}</td></tr>`;
                        orderTableBody.innerHTML += row;
                    });
                })
                .catch(error => console.error('Error fetching data:', error));
        }
   
    
    
        function toggleMenu() {
            const menu = document.getElementById('menu');
            menu.classList.toggle('open');
        }

        // Function to increment/decrement the range and number input values
function changeValue(id, step) {
    const rangeInput = document.getElementById(id);
    const numberInput = document.getElementById(id + 'Value');
    let newValue = parseInt(rangeInput.value) + step;

    // Ensure the new value is within the min and max range
    if (newValue >= parseInt(rangeInput.min) && newValue <= parseInt(rangeInput.max)) {
        rangeInput.value = newValue;
        numberInput.value = newValue;
    }
}

// Function to synchronize the range and number inputs
function syncInputs(sourceId, targetId) {
    document.getElementById(targetId).value = document.getElementById(sourceId).value;
}

document.querySelectorAll('.increment').forEach(button => {
    button.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const input = document.getElementById(targetId);
        let currentValue = parseInt(input.value);
        const maxValue = parseInt(input.getAttribute('max'));

        if (currentValue < maxValue) {
            input.value = currentValue + 1;
            updateRange(targetId);
        }
    });
});

document.querySelectorAll('.decrement').forEach(button => {
    button.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        const input = document.getElementById(targetId);
        let currentValue = parseInt(input.value);
        const minValue = parseInt(input.getAttribute('min'));

        if (currentValue > minValue) {
            input.value = currentValue - 1;
            updateRange(targetId);
        }
    });
});

function updateRange(targetId) {
    const input = document.getElementById(targetId);
    const rangeInput = document.getElementById(targetId.replace('Value', ''));
    rangeInput.value = input.value;
}



// dashboard page

function openTab(tabName, event) {
    // Hide all content by default
    var content = document.getElementsByClassName("dash-content");
    for (var i = 0; i < content.length; i++) {
        content[i].classList.remove("active");
    }

    // Remove the active class from all tabs
    var tabs = document.getElementsByClassName("dash-tab");
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
    }

    // Show the specific tab content
    document.getElementById(tabName).classList.add("active");

    // Add active class to the tab that was clicked
    event.currentTarget.classList.add("active");
}

// event-active page




   
    
