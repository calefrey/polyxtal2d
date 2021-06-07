Requirements:

* Scipy
* matplotlib

Before committing, format using the Black formatter

To get absolute references (using coordinates) out of the abaqus .rpy files instead of by "mesh number", run the following in the command window

`session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)`

To get references using the native python syntax (lists, etc) enter the following in the command window

`session.journalOptions.setValues(replayGeometry=INDEX)`