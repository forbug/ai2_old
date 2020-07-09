from pathlib import Path
from typing import Tuple, Optional

from vistautils.iter_utils import only
from vistautils import parameters_only_entrypoint
from vistautils.parameters import Parameters, YAMLParametersLoader
from pegasus_wrapper import (
    initialize_vista_pegasus_wrapper,
    directory_for,
    # experiment_directory,
    run_python_on_parameters,
    write_workflow_description,
)
from pegasus_wrapper.resource_request import ResourceRequest
from pegasus_wrapper.locator import Locator
from pegasus_wrapper.artifact import ValueArtifact


def main(params: Parameters):
    initialize_vista_pegasus_wrapper(params)

    parameter_options = params.namespace('parameter_options').as_mapping()
    print(parameter_options)

    # Compute all possible combinations of the parameters
    parameter_combinations = [[]]
    for parameter_name, options in parameter_options.items():
        new_combinations = []
        for combination in parameter_combinations:
            for option in options:
                new_combination = combination + [(parameter_name, option)]
                new_combinations.append(new_combination)
        parameter_combinations = new_combinations

    model_outputs_locator = Locator(('models',))
    jobs_info = []
    for i, combination in enumerate(parameter_combinations):
        task: str = only(option for parameter, option in combination if parameter == 'task')
        model: str = only(option for parameter, option in combination if parameter == 'model')
        task2: Optional[str] = next(
            (option for parameter, option in combination if parameter == 'task'),
            default=None,
        )
        train_data_slice: str = only(option for parameter, option in combination if parameter == 'train_data_slice')
        options: Tuple[str] = tuple(option for _, option in combination if option != '')
        locator = model_outputs_locator / Locator(options)

        # os.system(f"sbatch "
        #           # Additional SLURM specifications
        #           f"-J {experiment_id} "
        #           f"-o outputs/slurm/{experiment_id}.out "
        #           # Ephemeral specifications - sudo sacctmgr modify user beser set MaxJobs=25
        #           f"{'' if 'alphanli' in experiment_id else '--partition=ephemeral --qos=ephemeral --time=12:00:00 '}"
        #           f"slurm/run_saga.sh "
        #           # Python script commands
        #           f"\""
        #           f"{' '.join([f'{name}={option}' for name,option in combination  if option != ''])}"
        #           f" save_path={experiment_id}"
        #           f" save_best_only=False"
        #           f"{' batch_size=2' if 'hellaswag' in experiment_id else ''}"
        #           f"\"")
        # TODO: Special logic for alphanli vs. not alphanli
        # TODO: Make sure I do this right with Slurm
        resource_request = ResourceRequest.from_parameters(params)
        # slurm_output_path = directory_for(locator) / 'slurm.out'
        save_path = directory_for(locator)

        # Set up job parameters
        job_params = Parameters()
        project_root = params.existing_directory('project_root')
        for parameter, option in combination:
            parameter_directory = project_root / parameter
            if parameter_directory.exists():
                option_params: Parameters = YAMLParametersLoader().load(
                    parameter_directory / f'{option}.params'
                )
                job_params = job_params.unify(option_params)

        job_params = job_params.unify(Parameters.from_mapping(dict(combination)))
        job_params = job_params.unify({
            'save_path': save_path,
            'save_best_only': False,
            # Add to one of the params files:
            # (probably train-roberta-large-piqa.params)
            # SBATCH --cpus-per-task=4
            # num_cpus: 4  # add to a config
            'num_cpus': 4,
            # SBATCH --gpus-per-task=1
            # num_gpus: 1  # add to a config
            'num_gpus': 1,
            # SBATCH --mem-per-cpu=4g
            # memory: 4g
            'mem': '4g',
            # SBATCH --ntasks=1  # ALREADY COVERED, resource_request.py line 133
            # SBATCH --time=20:00:00  # TODO: not sure how to cover
        })
        job = run_python_on_parameters(
            locator,
            "train",
            # Pass some kind of parameters here to tell train.py where to put our stuff.
            job_params,
            # TODO maybe depend on the input file? however I specify that... I don't think I need to
            #  though.
            depends_on=[],
            # TODO set this up right, make sure it's using Slurm with the right parameters
            resource_request=resource_request
        )
        jobs_info.append({
            'job': job,
            'task': task,
            'train_data_slice': train_data_slice,
            'parameter_combination': combination,
            'predictions': ValueArtifact(locator=locator, value=save_path / 'predictions.lst'),
            'confidence': ValueArtifact(locator=locator, value=save_path / 'confidence.lst'),
        })

    # TODO: Run ensembling

    write_workflow_description()


if __name__ == '__main__':
    parameters_only_entrypoint(main)
