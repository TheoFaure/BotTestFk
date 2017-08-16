function compute_utt_answers(url) {
    $.ajax({
        type:"GET",
        url:"/framework/compute_answers/",
        success: function(response) {
            var context = JSON.parse(response);
            $('#nb_missing_answers').html(context['nb_missing_answers']);
            $('#acc').html(context['accuracies']);
            $('#error').html("");
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('#error').html("" + xhr.status + thrownError);
        }
    });
}

function compute_mut_answers(url) {
    $.ajax({
        type:"GET",
        url:"/framework/mutants_answers/",
        success: function(response) {
            var context = JSON.parse(response);
            $('#nb_missing_answers').html(context['nb_missing_answers']);
            $('#error').html("");
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('#error').html("" + xhr.status + thrownError);
        }
    });
}

$('#display-good-answers').click(function() { $(".good-answer").toggle(); });
