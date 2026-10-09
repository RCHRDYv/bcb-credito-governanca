"""
PT: Correção das respostas do assistente contra o gabarito (#48, ADR 0030).
    O corretor por script confere os valores pelo evaluation/comparacao.yml;
    a correção às cegas cobre a ressalva, a abstenção e a leitura declarada;
    o acerto junta os dois. A #50 reaproveita o pacote.

EN: Grading the assistant's answers against the answer key. The script
    grader checks values via comparacao.yml; blind grading covers caveat,
    abstention and declared reading; acerto combines both. Reused by #50.
"""
