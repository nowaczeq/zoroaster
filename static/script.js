document.addEventListener('DOMContentLoaded', function()
{
    let moodbuttons = document.querySelectorAll('.btn-secondary');
    let moods = [];
    moodbuttons.forEach(function(button)
    {
        button.addEventListener('click', function(e)
        {
            let val = button.value;
            if (!moods.includes(val))
            {
                moods[moods.length] = val;
            }
            e.preventDefault();
            this.style.background ='#000000';
        });
    });

    document.querySelector('.submitmoods').addEventListener('click', function(e)
    {
        let data = JSON.stringify(moods);
        fetch('/process_moods',
        {
            method: 'POST',
            body: data,
            headers: {'Content-Type': 'application/json'}
        });
    });
});