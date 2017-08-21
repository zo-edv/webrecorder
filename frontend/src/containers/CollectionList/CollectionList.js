import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { asyncConnect } from 'redux-connect';
import { fromJS } from 'immutable';
import { Link } from 'react-router';
import { Button, Col, ProgressBar, Row } from 'react-bootstrap';

import { sumCollectionsSize } from 'redux/selectors';

import { isLoaded as areCollsLoaded,
         load as loadCollections } from 'redux/modules/collections';
import { isLoaded as isAuthLoaded } from 'redux/modules/auth';
import { load as loadUser, isLoaded as isUserLoaded } from 'redux/modules/user';


import SizeFormat from 'components/SizeFormat';

import './style.scss';


class CollectionList extends Component {

  static propTypes = {
    collections: PropTypes.object,
    collSum: PropTypes.number,
    auth: PropTypes.object,
    user: PropTypes.object,
    params: PropTypes.object
  }

  static defaultProps = fromJS({
    collections: []
  })

  render() {
    const userParam = this.props.params.user;
    const { auth, collSum, user } = this.props;
    const collections = this.props.collections.get('collections');

    const canAdmin = auth.getIn(['user', 'username']) === userParam; // && !anon;
    const totalSpace = user.getIn(['data', 'space_utilization', 'total']);

    return (
      <div>
        <Row className="collection-description page-archive">
          <Col xs={12}>
            <h2>{ userParam } Archive</h2>
            <p>Available collections are listed below.</p>
          </Col>
        </Row>
        <Row>
          <Col xs={6} className="wr-coll-meta">
            {
              canAdmin &&
                <Button bsStyle="primary" bsSize="small">
                  <span className="glyphicon glyphicon-plus glyphicon-button" /> New Collection
                </Button>
            }
          </Col>
          {
            canAdmin &&
              <Col xs={2} className="pull-right">
                <strong>Space Used: </strong>
                <SizeFormat bytes={collSum} />
                <ProgressBar now={(collSum / totalSpace) * 100} bsStyle="success" />
              </Col>
          }
        </Row>

        {
          collections &&
            <Row>
              <ul className="list-group collection-list">
                { collections.sortBy(coll => coll.get('created_at')).map((coll) => {
                  return (
                    <li className="left-buffer list-group-item" key={coll.get('id')}>
                      <Row>
                        <Col xs={9}>
                          <Link to={`${userParam}/${coll.get('id')}`} className="collection-title">{coll.get('title')}</Link>
                        </Col>
                        <Col xs={2}>
                          <SizeFormat bytes={coll.get('size')} />
                        </Col>
                        <Col xs={1}>
                          { coll.get('r:@public') === '1' &&
                            <span className="glyphicon glyphicon-globe" title="Public Collection &mdash; Visible to Everyone" />
                          }
                        </Col>
                      </Row>
                    </li>);
                })
                }
              </ul>
            </Row>
        }

      </div>
    );
  }
}

const preloadCollections = [
  {
    promise: ({ params, store: { dispatch, getState } }) => {
      const state = getState();
      const collections = state.get('collections');
      const { user } = params;

      if(!areCollsLoaded(state) || (collections.get('user') === user &&
         Date.now() - collections.get('accessed') > 15 * 60 * 1000)) {
        return dispatch(loadCollections(user));
      }

      return undefined;
    }
  },
  {
    promise: ({ store: { dispatch, getState } }) => {
      const state = getState();

      if(isAuthLoaded(state) && !isUserLoaded(state))
        return dispatch(loadUser(state.getIn(['auth', 'user', 'username'])));

      return undefined;
    }
  }
];

const mapStateToProps = (state) => {
  const collections = state.get('collections');
  return {
    auth: state.get('auth'),
    collections,
    collSum: collections ? sumCollectionsSize(collections) : 0,
    user: state.get('user')
  };
};

export default asyncConnect(
  preloadCollections,
  mapStateToProps
)(CollectionList);