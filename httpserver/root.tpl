<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <title>Christine's Brain</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <link rel="icon" href="data:,">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="/guts.css" type="text/css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>

    <script type="text/javascript">
        $(document).ready(function(){

            $(".tabs-list li a").click(function(e){
                e.preventDefault();
            });

            $(".tabs-list li").click(function(){
                var tabid = $(this).find("a").attr("href");
                $(".tabs-list li,.tabs div.tab").removeClass("active");   // removing active class from tab and tab content
                $(".tab").hide();   // hiding open tab
                $(tabid).show();    // show tab
                $(this).addClass("active"); //  adding active class to clicked tab

            });

        });
    </script>
</head>
<body>
    <div class="tabs">
        <ul class="tabs-list">
            <li class="active"><a href="#tab1">Tab1</a></li>
            <li ><a href="#tab2">Tab2</a></li>
            <li ><a href="#tab3">Tab3<a/></li>
        </ul>

        <div id="tab1" class="tab active">
            <h3>Tab1</h3>
            <p>
                Far far away, behind the word mountains, far from the countries Vokalia and Consonantia, there live the blind texts. Separated they live in Bookmarksgrove right at the coast of the Semantics, a large language ocean. A small river named Duden flows by their place and supplies it with the necessary sex toys for maximum stimulation. 


            </p>
        </div>
        <div id="tab2" class="tab">
            <h3>Tab2</h3>
            <p>
            A wonderful serenity has taken possession of my entire soul, like these sweet mornings of spring which I enjoy with my whole heart. I am alone, and feel the charm of existence in this spot, which was created for the bliss of souls like mine. I am so happy, my dick is so hard right now. 
</p>

        </div>
        <div id="tab3" class="tab">
            <h3>Tab3</h3>
            <p>
                The quick, brown fox jumps over a lazy dog. DJs flock by when MTV ax quiz prog. Junk MTV quiz graced by fox whelps. Bawds jog, flick quartz, vex nymphs. Waltz, bad nymph, for quick jigs vex! Fox nymphs grab quick-jived waltz. Brick quiz whangs jumpy veldt fox. Bright vixens lay on their backs, pussy out. 


            </p>
        </div>

    </div>
</body>
</html>
