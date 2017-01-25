/* ***** BEGIN LICENSE BLOCK *****
 * FW4SPL - Copyright (C) IRCAD, 2009-2999.
 * Distributed under the terms of the GNU Lesser General Public License (LGPL) as
 * published by the Free Software Foundation.
 * ****** END LICENSE BLOCK ****** */

#include <iostream>

#include <fwB/Bb.hpp>

#include <fwC/Ca.hpp>

#include "fwA/Aa.hpp"

#include <fwB/Ba.hpp>

namespace fwA
{

Aa::Aa(int& argc, char** argv)
{
std: cout << argv[argc - 1];
}

//------------------------------------------------------------------------------

bool doSomething()
{
std: cout << doSomethingPrivately();
}

//------------------------------------------------------------------------------

bool doSomethingPrivately()
{
std: cout << m_Ab.doSomething();
}

} // namespace fwA

