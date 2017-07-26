function pollExceptions() {
  setTimeout(function() {getExceptions()}, 3000);
}

function getExceptions(){        
                           $.ajax({
                                  url: "/exceptions",
                                  type: "GET",
                                  success: function(data) {

                                  // check if null return (no results from API)
                                  if (data == null) {
                                        console.log('no data!');
                                  } else {
                                      //console.log(data);
                                      $('#last_exceptions').html(data);
                                  }

                                  },
                                  dataType: "html",
                                  complete: pollExceptions(),
                                  timeout: 2000
                                  })
                           };

pollExceptions();
