$("#import-csv-form").submit(importCSV);

String.prototype.format = String.prototype.f = function() {
  let s = this,
    i = arguments.length;

  while (i--) {
    s = s.replace(new RegExp("\\{" + i + "\\}", "gm"), arguments[i]);
  }
  return s;
};

const modalTpl =
  '<div class="modal fade" tabindex="-1" role="dialog">' +
  '  <div class="modal-dialog" role="document">' +
  '    <div class="modal-content">' +
  '      <div class="modal-header">' +
  '        <h5 class="modal-title">{0}</h5>' +
  '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
  '          <span aria-hidden="true">&times;</span>' +
  "        </button>" +
  "      </div>" +
  '      <div class="modal-body">' +
  "      </div>" +
  '      <div class="modal-footer">' +
  "      </div>" +
  "    </div>" +
  "  </div>" +
  "</div>";

const progressTpl =
  '<div class="progress">' +
  '  <div class="progress-bar progress-bar-success progress-bar-striped progress-bar-animated" role="progressbar" style="width: {0}%">' +
  "  </div>" +
  "</div>";

const errorTpl =
  '<div class="alert alert-danger alert-dismissable" role="alert">\n' +
  '  <span class="sr-only">Error:</span>\n' +
  "  {0}\n" +
  '  <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>\n' +
  "</div>";

const successTpl =
  '<div class="alert alert-success alert-dismissable submit-row" role="alert">\n' +
  "  <strong>Success!</strong>\n" +
  "  {0}\n" +
  '  <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>\n' +
  "</div>";


function ezProgressBar(args) {
  if (args.target) {
    const obj = $(args.target);
    const pbar = obj.find(".progress-bar");
    pbar.css("width", args.width + "%");
    return obj;
  }

  const modal = modalTpl.format(args.title);
  const progress = progressTpl.format(args.width);
  console.log(progress);
  //const modal = modalTpl.format(args.title);
  //const modal = $("#importCSV");
  const obj = $(modal);
  obj.find(".modal-body").append($(progress));

  //const obj = $("#importCSV");
  $(".container").append(obj);

  return obj.modal("show");
  //return obj
}

function importCSV(event) {
  event.preventDefault();
  if (document.getElementById("import-csv-file").files.length === 0){
      console.log('No CSV file selected');
  } 
  else {
  let csv_file = document.getElementById("import-csv-file").files[0];
  let csv_type = document.getElementById("csv_type").value;

  let form_data = new FormData();
  form_data.append("csv_file", csv_file);
  form_data.append("csv_type", csv_type);

  let pg = ezProgressBar({
    width: 0,
    title: "Upload Progress"
  });
    console.log(pg);


  $.ajax({
    url: "/admin/import/csv",
    type: "POST",
    data: form_data,
    processData: false,
    contentType: false,
    statusCode: {
      500: function(resp) {
        // Normalize errors
        let errors = JSON.parse(resp.responseText);
        let errorText = "";
        errors.forEach(element => {
            console.log(element);
            errorText += `${JSON.stringify(element)}\n`;
          /*
          errorText += `Line ${element[0]}: ${JSON.stringify(element[1])}\n`;
        */
        });

        // Show errors
        alert(errorText);

        // Hide progress modal if its there
        pg = ezProgressBar({
          target: pg,
          width: 100
        });
        setTimeout(function() {
          pg.modal('hide');
        }, 500);
      }
    },
    xhr: function() {
      let xhr = $.ajaxSettings.xhr();
      xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
          let width = (e.loaded / e.total) * 100;
          pg = ezProgressBar({
            target: pg,
            width: width
          });
        }
      };
      return xhr;
    },
    success: function(_data) {
      pg = ezProgressBar({
        target: pg,
        width: 100
      });
      setTimeout(function() {
        pg.modal("hide");
      }, 500);
      setTimeout(function() {
        window.location.reload();
      }, 700);
    }
  });
  } // End of if statement for detecting csv file is present
}
