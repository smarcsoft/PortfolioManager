export function encrypt(str:string, amount:number):string {  
    // Make an output variable
    var output = "";

    // Go through each character
    for (var i = 0; i < str.length; i++) {
        // Get the character we'll be appending
        var c = str[i];
  
        // Get its code
        var code = str.charCodeAt(i);
        c = String.fromCharCode(code + amount);

        // Append
        output += c;
    }
  
    // All done!
    return output;
  };

  