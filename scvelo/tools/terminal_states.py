from ..logging import logg, settings
from ..preprocessing.moments import get_connectivities
from .transition_matrix import transition_matrix
from .utils import scale
from scipy.sparse import linalg, csr_matrix
import numpy as np


def eigs(T, k=10, eps=1e-3, perc=None):
    eigvals, eigvecs = linalg.eigs(T.T, k=k, which='LR')  # find k eigs with largest real part
    p = np.argsort(eigvals)[::-1]                        # sort in descending order of eigenvalues
    eigvals = eigvals.real[p]
    eigvecs = eigvecs.real[:, p]

    idx = (eigvals >= 1 - eps)                           # select eigenvectors with eigenvalue of 1
    eigvals = eigvals[idx]
    eigvecs = np.absolute(eigvecs[:, idx])

    if perc is not None:
        lbs, ubs = np.percentile(eigvecs, perc, axis=0)
        eigvecs[eigvecs < lbs] = 0
        eigvecs = np.clip(eigvecs, 0, ubs)
        eigvecs /= eigvecs.max(0)

    return eigvals, eigvecs


def terminal_states(adata, vkey='velocity', self_transitions=False, basis=None, weight_diffusion=0, scale_diffusion=1,
                    eps=1e-3, copy=False):
    connectivities = get_connectivities(adata, 'distances')

    logg.info('computing root cells', r=True, end=' ')
    T = transition_matrix(adata, vkey=vkey, basis=basis, weight_diffusion=weight_diffusion,
                          scale_diffusion=scale_diffusion, self_transitions=self_transitions, backward=True)
    eigvecs = eigs(T, eps=eps, perc=[2, 98])[1]
    eigvec = csr_matrix.dot(connectivities, eigvecs).sum(1)
    eigvec = np.clip(eigvec, 0, np.percentile(eigvec, 98))
    adata.obs['root'] = scale(eigvec)
    logg.info('using ' + str(eigvecs.shape[1]) + ' eigenvectors with eigenvalue 1.')

    logg.info('computing end points', end=' ')
    T = transition_matrix(adata, vkey=vkey, basis=basis, weight_diffusion=weight_diffusion,
                          scale_diffusion=scale_diffusion, self_transitions=self_transitions, backward=False)
    eigvecs = eigs(T, eps=eps, perc=[2, 98])[1]
    eigvec = csr_matrix.dot(connectivities, eigvecs).sum(1)
    eigvec = np.clip(eigvec, 0, np.percentile(eigvec, 98))
    adata.obs['end'] = scale(eigvec)
    logg.info('using ' + str(eigvecs.shape[1]) + ' eigenvectors with eigenvalue 1.')

    logg.info('    finished', time=True, end=' ' if settings.verbosity > 2 else '\n')
    logg.hint(
        'added to `.obs`\n'
        '    \'root\', root cells of Markov diffusion process\n'
        '    \'end\', end points of Markov diffusion process')
    return adata if copy else None
