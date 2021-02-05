#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { CacheTwitterCdkStack } from '../lib/cache_twitter_cdk-stack';

const app = new cdk.App();
new CacheTwitterCdkStack(app, 'CacheTwitterCdkStack');
