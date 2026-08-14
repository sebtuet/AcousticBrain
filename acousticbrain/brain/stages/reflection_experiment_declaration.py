from acousticbrain.models import ControlledReflectionExperimentDeclaration


class ControlledReflectionExperimentDeclarationStage:
    """Copies explicitly loaded declarations without interpreting their content."""

    def run(self, project, context):
        declarations = tuple(project.controlled_reflection_experiment_declarations)
        if any(
            not isinstance(item, ControlledReflectionExperimentDeclaration)
            for item in declarations
        ):
            raise ValueError("Project reflection declarations are invalid.")
        context.controlled_reflection_experiment_declarations = tuple(
            sorted(declarations, key=lambda item: item.declaration_id)
        )
