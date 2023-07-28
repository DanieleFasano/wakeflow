# v_perts_only.py
# Written by Thomas Hilder

"""
Contains the _VelocityPerturbations class, intended for returning only velocity perturbations and not creating files, idea for use in a fitting procedure.
"""

import subprocess, os
import numpy as np
from .model_setup         import _run_setup, _Parameters
from .grid                import _Grid
from .linear_perts        import _LinearPerts
from .non_linear_perts    import _NonLinearPerts
from .wakeflow            import WakeflowModel
from typing               import Tuple


# class to generate velocity perturbations for models without saving to files
class _VelocityPerturbations(WakeflowModel):

    # generate the model using the configuration specified by the user
    def run(self) -> None:

        # check requirements for models for wakefit are satisfied (don't make files!)
        assert self.model_params["make_midplane_plots"] == False
        assert self.model_params["save_total"]          == False
        assert self.model_params["save_perturbations"]  == False
        
        # run setup
        try:
            params = _run_setup(self.model_params)
        except ArithmeticError:
            raise Exception("Model has not been configured.")

        # run wakeflow using custom method for wakefit
        return self._run_wakeflow(params)

    # internal method that is called by self.run to generate the results for a specific set of parameters
    # overwrites inherited method
    def _run_wakeflow(self, params: _Parameters) -> Tuple[np.ndarray, ...]:
        """
        Internal use method for generating the planet wake by calling other parts of Wakeflow.

        Parameters
        ----------
        params : Parameters 
            Paramaters object specfiying options for the model to be generated.
        """

        print("Extracting linear perturbations nearby planet")

        # make empty grid for linear perturbations
        grid_lin_perts = _Grid(params)
        grid_lin_perts._make_grid()
        grid_lin_perts._make_empty_disk()

        # extract linear perturbations from file
        lin_perts = _LinearPerts(params)
        lin_perts._cut_annulus_segment()

        # add the linear perturbations onto grid
        grid_lin_perts._add_linear_perturbations(lin_perts, rho_background=0.0)

        # make empty grid for non-linear perturbations
        grid_nonlin_perts = _Grid(params)
        grid_nonlin_perts._make_grid()
        grid_nonlin_perts._make_empty_disk()

        # initialise non-linear perturbations
        nonlin_perts = _NonLinearPerts(params, grid_nonlin_perts)

        # extract initial condition from the linear perturbations
        nonlin_perts._extract_ICs_ann(lin_perts)

        # solve for non-linear perturbations
        nonlin_perts._get_non_linear_perts()

        # add non-linear perturbations to grid
        grid_nonlin_perts._add_non_linear_perturbations(nonlin_perts, rho_background=0.0)

        # merge grids for result
        grid_lin_perts._merge_grids(grid_nonlin_perts)

        # return the grid and velocity components
        return (grid_lin_perts.x, grid_lin_perts.y, grid_lin_perts.v_r, grid_lin_perts.v_phi)