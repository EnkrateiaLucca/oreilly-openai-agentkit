// Polyfill for crypto.randomUUID() to ensure ChatKit compatibility
// This runs before the ChatKit script loads to provide the missing API
if (typeof crypto !== 'undefined' && !crypto.randomUUID) {
  crypto.randomUUID = function() {
    // RFC4122 version 4 compliant UUID generator
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, function(c) {
      return (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16);
    });
  };
}
