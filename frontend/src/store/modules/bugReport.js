import { fromJS } from 'immutable';

import { apiPath } from 'config';


const REPORT = 'wr/bugReport/REPORT';
const REPORT_SUCCESS = 'wr/bugReport/REPORT_SUCCESS';
const REPORT_FAIL = 'wr/bugReport/REPORT_FAIL';

const TOGGLE_MODAL = 'wr/bugReport/TOGGLE_MODAL';
const CONTACT_SUPPORT = 'wr/bugReport/CONTACT_SUPPORT';
const CONTACT_SUPPORT_SUCCESS = 'wr/bugReport/CONTACT_SUPPORT_SUCCESS';
const CONTACT_SUPPORT_FAIL = 'wr/bugReport/CONTACT_SUPPORT_FAIL';
const initialState = fromJS({
  reportModal: null,
  submitting: false,
  submitted: false,
  error: null
});

export default function bugReport(state = initialState, action = {}) {
  switch (action.type) {
    case TOGGLE_MODAL:
      return state.set('reportModal', action.reportType);
    case REPORT:
      return state.merge({
        submitting: true,
        submitted: false
      });
    case CONTACT_SUPPORT:
      return state.set('error', action.result);
    case REPORT_SUCCESS:
      return state.merge({
        submitting: false,
        submitted: true,
        error: null
      });
    case REPORT_FAIL:
      return state.merge({
        submitting: false,
        submitted: false,
        error: true
      });
    default:
      return state;
  }
}

export function toggleModal(reportType = 'dnlr') {
  return {
    type: TOGGLE_MODAL,
    reportType
  };
}
export function sendContactDispatch(postData) {
  return {
    types: [CONTACT_SUPPORT, CONTACT_SUPPORT_SUCCESS, CONTACT_SUPPORT_FAIL],
    promise: client => client.post(`${apiPath}/contact/support`, {
      data: {
        ...postData
      }
    })
  };
}

export function reportBug(postData, reportType = 'dnlr') {
  return {
    types: [REPORT, REPORT_SUCCESS, REPORT_FAIL],
    promise: client => client.post(`${apiPath}/report/${reportType}`, {
      data: {
        ...postData
      }
    })
  };
}
