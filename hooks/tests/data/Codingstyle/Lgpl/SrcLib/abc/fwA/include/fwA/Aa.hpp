/* ***** BEGIN LICENSE BLOCK *****
 * FW4SPL - Copyright (C) IRCAD, 2009-2000.
 * Distributed under the terms of the GNU Lesser General Public License (LGPL) as
 * published by the Free Software Foundation.
 * ****** END LICENSE BLOCK ****** */

#ifndef __FWA_AA_HPP__
#define __FWA_AA_HPP__

#include "fwA/Ab.hpp"

#include <fwB/fwB.hpp>

#include <fwC/fwC.hpp>

namespace fwA
{

class AA_CLASS_API Aa
{

public:

    AA_API Aa(int& argc, char** argv);

    AA_API bool doSomething();

private:

    Ab m_Ab;

    bool doSomethingPrivately();
};

} // namespace fwA

#endif // __FWA_AA_HPP__