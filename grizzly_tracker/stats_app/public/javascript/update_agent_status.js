function pollAgentStatus() {
  setTimeout(function() {getAgentStatus()}, 3000);
}

function getAgentStatus(){        
                           $.ajax({
                                  url: "/agent_status",
                                  type: "GET",
                                  success: function(data) {

                                  // check if null return (no results from API)
                                  if (data == null) {
                                        console.log('no data!');
                                  } else {
                                      //console.log(data);
                                      $('#agent_statuses').html(data);
                                  }

                                  },
                                  dataType: "html",
                                  complete: pollAgentStatus(),
                                  timeout: 2000
                                  })
                           };

pollAgentStatus();
