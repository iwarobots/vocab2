function submit_article() {
    article = $('#article-content').val();
    posting = $.post(
        '/reader',
        {"article": article},
        'json'
    );

    posting.done(
        function(data) {
            article = '<p>' + article + '</p>';

            while (article.search('\n') != -1) {
                article = article.replace('\n', '</p><p>');
            }

            for (i=0; i<data.spellings.length; i++) {
                var s = data.spellings[i];
                var cs = s.charAt(0).toUpperCase() + s.slice(1);

                var re = RegExp(s, 'g');
                article = article.replace(
                    re,
                    '<mark title="' + data.definitions[i] + '">' + s + '</mark>'
                );

                var re = RegExp(cs, 'g');
                article = article.replace(
                    cs,
                    '<mark title="' + data.definitions[i] + '">' + cs + '</mark>'
                );
            }

            $('#article-display').html(article);
        })
}

function get_selected_word () {
    var word = document.getSelection().toString();
    return word
}

function add_selected () {
    var word = get_selected_word();
    if (word != '') {
        $('#word-table').append('<tr><td>' + word + '</td><td class="definition_undownloaded"><button id="view-definitions" class="btn btn-success">View definitions</button></td></tr>');
    }
}

function download_definitions(word) {

}


function display_definitions() {

}


$(document).ready(function() {
    $('#add').click(function() {
        add_selected();
    });
});
