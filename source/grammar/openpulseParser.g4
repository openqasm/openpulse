/***** ANTLRv4  grammar for OpenPulse. *****/
// This grammar is OpenPulse extension for QOpenQASM3.0
// We introduce several new types for OpenPulse.
// We override several nodes in qasm3 to consume the new types.
// The OpenPulse grammar can be used inside cal or defcal blocks.

parser grammar openpulseParser;
import qasm3Parser;

options {
    tokenVocab = openpulseLexer;
}

calibrationBlock: openpulseStatement*;

openpulseStatement:
    // Statements can be used in the cal or defcal body
    pragma
    | annotation* (
        aliasDeclarationStatement
        | assignmentStatement
        | barrierStatement
        | boxStatement
        | breakStatement
        | classicalDeclarationStatement
        | constDeclarationStatement
        | continueStatement
        | defStatement
        | delayStatement
        | endStatement
        | expressionStatement
        | externStatement
        | externFrameStatement
        | externPortStatement
        | forStatement
        | gateCallStatement
        | ifStatement
        | includeStatement
        | ioDeclarationStatement
        | quantumDeclarationStatement
        | resetStatement
        | returnStatement
        | switchStatement
        | whileStatement
    )
;

/** In the following we extend existing OpenQASM nodes. Need to refresh whenever OpenQASM is updated. **/
// We extend the scalarType with WAVEFORM, PORT and FRAME
scalarType:
    BIT designator?
    | INT designator?
    | UINT designator?
    | FLOAT designator?
    | ANGLE designator?
    | BOOL
    | DURATION
    | STRETCH
    | COMPLEX (LBRACKET scalarType RBRACKET)?
    | WAVEFORM
    | PORT
    | FRAME
    ;


externFrameStatement: EXTERN FRAME Identifier SEMICOLON;
externPortStatement: EXTERN PORT Identifier SEMICOLON;
