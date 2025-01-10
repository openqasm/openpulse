import dataclasses

import pytest
from openpulse.ast import (
    AngleType,
    Annotation,
    ArrayLiteral,
    ArrayType,
    AssignmentOperator,
    CalibrationDefinition,
    CalibrationStatement,
    ClassicalArgument,
    ClassicalAssignment,
    ClassicalDeclaration,
    ComplexType,
    CompoundStatement,
    DurationType,
    ExpressionStatement,
    ExternArgument,
    ExternDeclaration,
    FloatLiteral,
    FloatType,
    ForInLoop,
    FrameType,
    FunctionCall,
    Identifier,
    IntegerLiteral,
    IntType,
    PortType,
    Pragma,
    Program,
    QASMNode,
    QuantumBarrier,
    RangeDefinition,
    ReturnStatement,
    SwitchStatement,
    UnaryExpression,
    UnaryOperator,
    WaveformType,
)
from openpulse.parser import parse, OpenPulseParsingError
from openqasm3.visitor import QASMVisitor


class SpanGuard(QASMVisitor):
    """Ensure that we did not forget to set spans when we add new AST nodes"""

    def visit(self, node: QASMNode):
        try:
            assert node.span is not None
            return super().visit(node)
        except Exception as e:
            raise Exception(f"The span of {type(node)} is None.") from e


def _remove_spans(node):
    """Return a new ``QASMNode`` with all spans recursively set to ``None`` to
    reduce noise in test failure messages."""
    if isinstance(node, list):
        return [_remove_spans(item) for item in node]
    if not isinstance(node, QASMNode):
        return node
    kwargs = {}
    no_init = {}
    for field in dataclasses.fields(node):
        if field.name == "span":
            continue
        target = kwargs if field.init else no_init
        target[field.name] = _remove_spans(getattr(node, field.name))
    out = type(node)(**kwargs)
    for attribute, value in no_init.items():
        setattr(out, attribute, value)
    return out


def test_calibration_definition():
    p = """
    defcal rz(angle[20] theta) $1 { return shift_phase(drive($1), -theta); }
    """.strip()
    program = parse(p)
    assert _remove_spans(program) == Program(
        statements=[
            CalibrationDefinition(
                name=Identifier("rz"),
                arguments=[
                    ClassicalArgument(
                        type=AngleType(size=IntegerLiteral(20)),
                        name=Identifier("theta"),
                    )
                ],
                qubits=[Identifier("$1")],
                return_type=None,
                body=[
                    ReturnStatement(
                        expression=FunctionCall(
                            name=Identifier(name="shift_phase"),
                            arguments=[
                                FunctionCall(
                                    name=Identifier(name="drive"),
                                    arguments=[Identifier(name="$1")],
                                ),
                                UnaryExpression(
                                    op=UnaryOperator["-"],
                                    expression=Identifier(name="theta"),
                                ),
                            ],
                        )
                    )
                ],
            )
        ]
    )
    SpanGuard().visit(program)


def test_calibration():
    p = """
    cal {
        extern drag(complex[float[size]], duration, duration, float[size]) -> waveform;

        port q0;

        frame q0_frame = newframe(q0, 0);
    }
    """.strip()
    program = parse(p)
    assert _remove_spans(program) == Program(
        statements=[
            CalibrationStatement(
                body=[
                    ExternDeclaration(
                        name=Identifier("drag"),
                        arguments=[
                            ExternArgument(
                                type=ComplexType(
                                    base_type=FloatType(size=Identifier("size")),
                                )
                            ),
                            ExternArgument(type=DurationType()),
                            ExternArgument(type=DurationType()),
                            ExternArgument(type=FloatType(Identifier("size"))),
                        ],
                        return_type=WaveformType(),
                    ),
                    ClassicalDeclaration(
                        type=PortType(),
                        identifier=Identifier(name="q0"),
                        init_expression=None,
                    ),
                    ClassicalDeclaration(
                        type=FrameType(),
                        identifier=Identifier(name="q0_frame"),
                        init_expression=FunctionCall(
                            name=Identifier(name="newframe"),
                            arguments=[Identifier(name="q0"), IntegerLiteral(value=0)],
                        ),
                    ),
                ]
            )
        ]
    )
    SpanGuard().visit(program)


def test_calibration2():
    p = """
        cal {
            port tx_port;
            frame tx_frame = newframe(tx_port, 7883050000.0, 0);
            waveform readout_waveform_wf = constant(5e-06, 0.03);
            for int shot in [0:499] {
                play(readout_waveform_wf, tx_frame);
                barrier tx_frame;
            }
        }
    """.strip()
    program = parse(p)
    assert _remove_spans(program) == Program(
        statements=[
            CalibrationStatement(
                body=[
                    ClassicalDeclaration(
                        type=PortType(),
                        identifier=Identifier(name="tx_port"),
                        init_expression=None,
                    ),
                    ClassicalDeclaration(
                        type=FrameType(),
                        identifier=Identifier(name="tx_frame"),
                        init_expression=FunctionCall(
                            name=Identifier(name="newframe"),
                            arguments=[
                                Identifier(name="tx_port"),
                                FloatLiteral(value=7883050000.0),
                                IntegerLiteral(value=0),
                            ],
                        ),
                    ),
                    ClassicalDeclaration(
                        type=WaveformType(),
                        identifier=Identifier(name="readout_waveform_wf"),
                        init_expression=FunctionCall(
                            name=Identifier(name="constant"),
                            arguments=[
                                FloatLiteral(value=5e-06),
                                FloatLiteral(value=0.03),
                            ],
                        ),
                    ),
                    ForInLoop(
                        type=IntType(),
                        identifier=Identifier(name="shot"),
                        set_declaration=RangeDefinition(
                            start=IntegerLiteral(value=0),
                            end=IntegerLiteral(value=499),
                            step=None,
                        ),
                        block=[
                            ExpressionStatement(
                                expression=FunctionCall(
                                    name=Identifier(name="play"),
                                    arguments=[
                                        Identifier(name="readout_waveform_wf"),
                                        Identifier(name="tx_frame"),
                                    ],
                                ),
                            ),
                            QuantumBarrier(
                                qubits=[
                                    Identifier(name="tx_frame"),
                                ],
                            ),
                        ],
                    ),
                ]
            )
        ]
    )
    SpanGuard().visit(program)


def test_array():
    p = """
    cal {
        array[int[32], 4] my_array = {3, 4, 5, 5};
    }
    """.strip()
    program = parse(p)
    assert _remove_spans(program) == Program(
        statements=[
            CalibrationStatement(
                body=[
                    ClassicalDeclaration(
                        type=ArrayType(
                            base_type=IntType(size=IntegerLiteral(value=32)),
                            dimensions=[IntegerLiteral(value=4)],
                        ),
                        identifier=Identifier(name="my_array"),
                        init_expression=ArrayLiteral(
                            values=[
                                IntegerLiteral(value=3),
                                IntegerLiteral(value=4),
                                IntegerLiteral(value=5),
                                IntegerLiteral(value=5),
                            ],
                        ),
                    )
                ]
            )
        ]
    )
    SpanGuard().visit(program)


def test_annotation_in_cal_block():
    p = """
    cal {
      @word1
      int x = 10;

      @word1 command1
      @word2 command2 32f%^&
      x = 0;

      @word1 @not_a_separate_annotation uint x;
      z();
    }
    """

    xdecl = ClassicalDeclaration(
        type=IntType(),
        identifier=Identifier("x"),
        init_expression=IntegerLiteral(10),
    )
    xdecl.annotations = [Annotation("word1")]

    xassign = ClassicalAssignment(Identifier("x"), AssignmentOperator["="], IntegerLiteral(0))
    xassign.annotations = [Annotation("word1", "command1"), Annotation("word2", "command2 32f%^&")]

    zcall = ExpressionStatement(FunctionCall(Identifier("z"), []))
    zcall.annotations = [Annotation("word1", "@not_a_separate_annotation uint x;")]
    program = parse(p)
    expected = Program(statements=[CalibrationStatement(body=[xdecl, xassign, zcall])])

    assert _remove_spans(program) == expected


def test_pragma_in_cal_block():
    p = """
    cal {
      #pragma foo bar
      int x = 10;
    }
    """

    program = parse(p)
    expected = Program(
        statements=[
            CalibrationStatement(
                body=[
                    Pragma(command="foo bar"),
                    ClassicalDeclaration(
                        type=IntType(),
                        identifier=Identifier("x"),
                        init_expression=IntegerLiteral(10),
                    ),
                ]
            )
        ]
    )
    assert _remove_spans(program) == expected


def test_switch_in_cal_block():
    p = """
    cal {
      switch (x) {
        case 1, 2 {}
        case 3 {}
        default {}
      }
    }
    """

    program = parse(p)
    expected = Program(
        statements=[
            CalibrationStatement(
                body=[
                    SwitchStatement(
                        target=Identifier(name="x"),
                        cases=[
                            (
                                [IntegerLiteral(value=1), IntegerLiteral(value=2)],
                                CompoundStatement(statements=[]),
                            ),
                            (
                                [IntegerLiteral(value=3)],
                                CompoundStatement(statements=[]),
                            ),
                        ],
                        default=CompoundStatement(statements=[]),
                    )
                ]
            )
        ]
    )
    assert _remove_spans(program) == expected


def test_permissive_parsing(capsys):
    p = """
    cal {
      int;
    }
    """

    with pytest.raises(AttributeError, match=r"'NoneType' object has no attribute 'line'"):
        # In this case, we do get an exception, but this is somewhat incidental --
        # the antlr parser gives us a `None` value where we expect a `Statement`
        parse(p, permissive=True)
    # The actual ANTLR failure is reported via stderr
    captured = capsys.readouterr()
    assert captured.err.strip() == "line 2:9 no viable alternative at input 'int;'"

    with pytest.raises(OpenPulseParsingError, match=r"Unexpected token ';' at line 2, column 10."):
        # This is stricter -- we fail as soon as ANTLR sees a problem
        parse(p)
    captured = capsys.readouterr()
    # The actual ANTLR failure is reported via stderr
    assert captured.err.strip() == "line 2:9 no viable alternative at input 'int;'"


@pytest.mark.parametrize(
    "p",
    [
        """
        cal {
            port xy_port;
            port tx_port;
            port rx_port;
            extern port cx_port;
            frame xy_frame = newframe(xy_port, 3714500000.0, 0);
            frame tx_frame = newframe(tx_port, 7883050000.0, 0);
            frame rx_frame = newframe(rx_port, 7883050000.0, 0);
            extern frame cx_frame;
            waveform rabi_pulse_wf = gaussian(1e-07, 2.5e-08, 1.0, 0.0);
            waveform readout_waveform_wf = constant(5e-06, 0.03);
            waveform readout_kernel_wf = constant(5e-06, 1.0);
            for int shot in [0:499] {
                set_scale(0.0, xy_frame);
                for int amp in [0:50] {
                    set_frequency(3714500000.0, xy_frame);
                    delay[200000.0ns] xy_frame, tx_frame, rx_frame;
                    set_phase(0, xy_frame);
                    play(rabi_pulse_wf, xy_frame);
                    barrier xy_frame, tx_frame, rx_frame;
                    set_phase(0, tx_frame);
                    set_phase(0, rx_frame);
                    play(readout_waveform_wf, tx_frame);
                    capture(readout_kernel_wf, rx_frame);
                    barrier xy_frame, tx_frame, rx_frame;
                    shift_scale(0.018000000000000002, xy_frame);
                }
            }
        }
        """,
    ],
)
def test_parsing(p: str):
    parse(p)
